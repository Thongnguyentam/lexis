from __future__ import annotations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import re
from typing import Optional, Tuple, List, Union, Literal
import base64
import matplotlib.pyplot as plt
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import os
from mistralai import Mistral
from dataclasses import dataclass, asdict
from textwrap import dedent
from streamlit_agraph import agraph, Node, Edge, Config
from prompts.system_prompts import (
    MINDMAP_SYSTEM_PROMPT,
    MINDMAP_INSTRUCTION_PROMPT,
    MINDMAP_EXAMPLE_CONVERSATION
)

NODE_COLOR = "#00CED1" 
SELECTED_NODE_COLOR = "#FF4500"

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

@dataclass
class Message:
    """Represents a message in a Mistral conversation.
    
    Attributes:
        content (str): The text content of the message
        role (Literal["user", "system", "assistant"]): The role of the message sender
    """
    content: str
    role: Literal["user", "system", "assistant"]

    def __post_init__(self):
        """Post-initialization hook to clean up message content.
        Removes indentation and extra whitespace."""
        self.content = dedent(self.content).strip()

START_CONVERSATION = [
    Message(MINDMAP_SYSTEM_PROMPT, role="system"),
    Message(MINDMAP_INSTRUCTION_PROMPT, role="user"),
]

# Add example conversation messages
for msg in MINDMAP_EXAMPLE_CONVERSATION:
    START_CONVERSATION.append(Message(msg["content"], role=msg["role"]))

def ask_mistral(conversation: List[Message]) -> Tuple[str, List[Message]]:
    """Send conversation to Mistral AI and get response.
    
    Args:
        conversation (List[Message]): List of previous messages in the conversation
        
    Returns:
        Tuple[str, List[Message]]: 
            - Generated response text
            - Updated conversation history including the new response
            
    Note: Uses mistral-large-latest model for optimal mind map generation
    """
    response = mistral_client.chat.complete(
        model="mistral-large-latest",
        messages=[asdict(c) for c in conversation]
    )
    msg = Message(
        content=response.choices[0].message.content,
        role="assistant"
    )
    return msg.content, conversation + [msg]

class MindMap:
    """Represents and manages an interactive mind map visualization.
    
    The mind map is stored as a graph structure with nodes and edges.
    Supports operations like:
    - Creating new mind maps from text prompts
    - Expanding existing nodes
    - Deleting nodes and their connections
    - Visualizing the graph interactively
    """
    
    def __init__(self, edges: Optional[List[Tuple[str, str]]]=None, nodes: Optional[List[str]]=None) -> None:
        """Initialize a new mind map.
        
        Args:
            edges (Optional[List[Tuple[str, str]]]): List of node pairs representing connections
            nodes (Optional[List[str]]): List of node labels/content
        """
        self.edges = [] if edges is None else edges
        self.nodes = [] if nodes is None else nodes
        self.save()

    @classmethod
    def load(cls) -> MindMap:
        """Load existing mind map from session state or create new one.
        
        Returns:
            MindMap: Retrieved or newly created mind map instance
        """
        if "mindmap" in st.session_state:
            return st.session_state["mindmap"]
        return cls()

    def save(self) -> None:
        """Save current mind map state to session storage for persistence."""
        st.session_state["mindmap"] = self

    def is_empty(self) -> bool:
        """Check if mind map has any content.
        
        Returns:
            bool: True if mind map has no edges, False otherwise
        """
        return len(self.edges) == 0
    
    def ask_for_initial_graph(self, query: str) -> None:
        """Generate a new mind map from scratch based on user query.
        
        Args:
            query (str): User's text prompt describing desired mind map content
            
        Process:
        1. Send query to Mistral AI with mind map generation prompt
        2. Parse response to extract node relationships
        3. Update graph structure with new nodes and edges
        """
        conversation = START_CONVERSATION + [
            Message(f"""
                Great, now ignore all previous nodes and restart from scratch. I now want you do the following:    

                {query}
            """, role="user")
        ]

        output, self.conversation = ask_mistral(conversation)
        self.parse_and_include_edges(output, replace=True)

    def ask_for_extended_graph(self, selected_node: Optional[str]=None, text: Optional[str]=None) -> None:
        """Expand the mind map from a selected node or based on text instruction.
        
        Args:
            selected_node (Optional[str]): Node to expand with new connections
            text (Optional[str]): Text description of how to modify the graph
            
        Note: At least one of selected_node or text must be provided
        """
        if (selected_node is None and text is None):
            return

        if selected_node is not None:
            conversation = self.conversation + [
                Message(f"""
                    add new edges to new nodes, starting from the node "{selected_node}"
                """, role="user")
            ]
            st.session_state.last_expanded = selected_node
        else:
            conversation = self.conversation + [Message(text, role="user")]

        output, self.conversation = ask_mistral(conversation)
        self.parse_and_include_edges(output, replace=False)

    def parse_and_include_edges(self, output: str, replace: bool=True) -> None:
        """Parse Mistral's output and update the graph structure.
        
        Args:
            output (str): Raw text output from Mistral containing add/delete commands
            replace (bool): If True, replace existing edges; if False, add to them
            
        Process:
        1. Extract add/delete commands using regex
        2. Process node and edge modifications
        3. Update graph while maintaining consistency
        4. Remove any duplicate edges
        """

        pattern1 = r'(add|delete)\("([^()"]+)",\s*"([^()"]+)"\)'
        pattern2 = r'(delete)\("([^()"]+)"\)'

        matches = re.findall(pattern1, output) + re.findall(pattern2, output)

        new_edges = []
        remove_edges = set()
        remove_nodes = set()
        for match in matches:
            op, *args = match
            add = op == "add"
            if add or (op == "delete" and len(args)==2):
                a, b = args
                if a == b:
                    continue
                if add:
                    new_edges.append((a, b))
                else:
                    # remove both directions
                    # (undirected graph)
                    remove_edges.add(frozenset([a, b]))
            else: # must be delete of node
                remove_nodes.add(args[0])

        if replace:
            edges = new_edges
        else:
            edges = self.edges + new_edges

        added = set()
        for edge in edges:
            nodes = frozenset(edge)
            if nodes in added or nodes & remove_nodes or nodes in remove_edges:
                continue
            added.add(nodes)

        self.edges = list([tuple(a) for a in added])
        self.nodes = list(set([n for e in self.edges for n in e]))
        self.save()

    def _delete_node(self, node) -> None:
        """Remove a node and all its connections from the graph.
        
        Args:
            node (str): Label of the node to delete
            
        Effects:
        - Removes all edges connected to the node
        - Updates node list to reflect changes
        - Records deletion in conversation history
        """
        self.edges = [e for e in self.edges if node not in frozenset(e)]
        self.nodes = list(set([n for e in self.edges for n in e]))
        self.conversation.append(Message(
            f'delete("{node}")', 
            role="user"
        ))
        self.save()

    def visualize(self) -> None | str:
        """Create interactive visualization of the mind map.
        
        Returns:
            Optional[str]: Label of clicked node if any, None otherwise
            
        Features:
        - Nodes sized based on selection status
        - Color coding for regular vs selected nodes
        - Interactive click handling
        - Automatic layout with physics simulation
        
        Note: Uses streamlit-agraph for rendering
        """
        try:
            selected = st.session_state.get("last_expanded")
            vis_nodes = [
                Node(
                    id=n, 
                    label=n, 
                    size=10+10*(n==selected), 
                    color=NODE_COLOR if n != selected else SELECTED_NODE_COLOR
                ) 
                for n in self.nodes
            ]
            vis_edges = [Edge(source=a, target=b) for a, b in self.edges]
            config = Config(width="100%",
                          height=500,
                          directed=False, 
                          physics=True,
                          hierarchical=False,
                          )
            clicked_node = agraph(nodes=vis_nodes, 
                            edges=vis_edges, 
                            config=config)
            
            return clicked_node
            
        except Exception as e:
            st.error(f"Visualization error: {str(e)}")
            return None

def main():
    """Main entry point for standalone mind map application.
    
    Features:
    - Sidebar input for mind map generation prompts
    - Persistent state management
    - Loading indicator during generation
    - Automatic rerun on updates
    """
    mindmap = MindMap.load()

    st.sidebar.title("AI Mind Map Generator")
    
    empty = mindmap.is_empty()
    query = st.sidebar.text_area(
        "Enter your prompt to generate a mind map", 
        value=st.session_state.get("mindmap-input", ""),
        key="mindmap-input",
        height=200
    )
    submit = st.sidebar.button("Submit")

    valid_submission = submit and query != ""

    if empty and not valid_submission:
        return

    with st.spinner(text="Loading..."):
        if valid_submission:
            mindmap.ask_for_initial_graph(query=query)
            st.rerun()
        else:
            mindmap.visualize()

if __name__ == "__main__":
    main()