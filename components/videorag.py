import sys
import tempfile
from typing import Tuple, Optional, Dict, List
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from mistralai import Mistral

# Handle SQLite version requirement for ChromaDB
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from chromadb import Client, Settings
import chromadb
import os
import uuid
import requests
import re
from datetime import datetime, timedelta

class VideoRAG:
    """Component for chatting with YouTube videos using Mistral AI and ChromaDB."""
    
    def __init__(self, mistral_client: Mistral):
        """Initialize VideoRAG with Mistral client and ChromaDB.
        
        Args:
            mistral_client: Initialized Mistral client
        """
        self.mistral_client = mistral_client
        
        # Create a unique directory for this instance
        self.temp_dir = os.path.join(tempfile.gettempdir(), f"chroma_{uuid.uuid4().hex}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize ChromaDB with unique persistence directory
        self.chroma_client = Client(Settings(
            persist_directory=self.temp_dir,
            anonymized_telemetry=False,
            is_persistent=True
        ))
        
        # Create a unique collection name
        collection_name = f"youtube_transcripts_{uuid.uuid4().hex[:8]}"
        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Store video metadata
        self.video_metadata = {}

    def extract_video_id(self, video_url: str) -> str:
        """Extract YouTube video ID from URL.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Video ID string
            
        Raises:
            ValueError: If URL format is invalid
        """
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[-1].split("&")[0]
        elif "youtube.com/shorts/" in video_url:
            return video_url.split("/shorts/")[-1].split("?")[0]
        elif "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[-1]
        else:
            raise ValueError("Invalid YouTube URL")

    def get_video_metadata(self, video_id: str) -> Dict:
        """Fetch video metadata using YouTube Data API or oEmbed.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dict containing video title, author, upload date and embed HTML
        """
        try:
            # Using oEmbed to get embed HTML and metadata
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url)
            data = response.json()
            
            # Get video page to parse upload date
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_page = requests.get(video_url)
            
            # Try to parse upload date from video page
            upload_date = datetime.now()  # fallback
            if video_page.status_code == 200:
                try:
                    # Look for uploadDate in the page content
                    date_match = re.search(r'"uploadDate":"([^"]+)"', video_page.text)
                    if date_match:
                        # Parse ISO 8601 format with timezone
                        iso_date = date_match.group(1)
                        # Extract just the date part (YYYY-MM-DD) from the ISO timestamp
                        upload_date = datetime.strptime(iso_date.split('T')[0], "%Y-%m-%d")
                except Exception as e:
                    st.warning(f"Could not parse upload date: {e}")
            
            # Store video info in session state for info panel
            st.session_state.current_video = {
                "id": video_id,
                "title": data.get("title", "Untitled Video"),
                "author": data.get("author_name", "Unknown Author"),
                "embed_html": data.get("html", ""),
                "url": video_url,
                "upload_date": upload_date
            }
            
            return {
                "title": data.get("title", "Untitled Video"),
                "author": data.get("author_name", "Unknown Author"),
                "upload_date": upload_date,
                "url": video_url
            }
        except Exception as e:
            st.error(f"Error fetching video metadata: {e}")
            return {
                "title": "Untitled Video",
                "author": "Unknown Author",
                "upload_date": datetime.now(),
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }

    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        time = timedelta(seconds=int(seconds))
        hours = time.seconds // 3600
        minutes = (time.seconds % 3600) // 60
        seconds = time.seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def fetch_video_data(self, video_url: str) -> Tuple[str, List[Dict]]:
        """Fetch transcript data from YouTube video with timestamps.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Tuple of (video_id, transcript entries with timestamps)
        """
        try:
            video_id = self.extract_video_id(video_url)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Fetch and store video metadata
            self.video_metadata[video_id] = self.get_video_metadata(video_id)
            
            return video_id, transcript
        except Exception as e:
            st.error(f"Error fetching transcript: {e}")
            return video_id, []

    def add_video_to_knowledge_base(self, video_url: str) -> bool:
        """Add video transcript with timestamps to ChromaDB knowledge base."""
        try:
            video_id, transcript = self.fetch_video_data(video_url)
            if transcript:
                # Combine transcript entries into meaningful chunks
                chunks = []
                current_chunk = {
                    "text": "",
                    "start_time": 0,
                    "duration": 0
                }
                
                for i, entry in enumerate(transcript):
                    # Start new chunk if current one is too long or ends with period
                    if (len(current_chunk["text"]) > 0 and 
                        (len(current_chunk["text"]) + len(entry["text"]) > 200 or 
                         current_chunk["text"].strip().endswith("."))):
                        chunks.append(current_chunk)
                        current_chunk = {
                            "text": "",
                            "start_time": entry["start"],
                            "duration": 0
                        }
                    
                    # Add entry to current chunk
                    if not current_chunk["text"]:
                        current_chunk["start_time"] = entry["start"]
                    current_chunk["text"] += " " + entry["text"]
                    current_chunk["duration"] = (entry["start"] + entry["duration"]) - current_chunk["start_time"]
                
                # Add final chunk if not empty
                if current_chunk["text"]:
                    chunks.append(current_chunk)
                
                # Add chunks to ChromaDB
                for i, chunk in enumerate(chunks):
                    self.collection.add(
                        documents=[chunk["text"].strip()],
                        metadatas=[{
                            "video_id": video_id,
                            "start_time": chunk["start_time"],
                            "duration": chunk["duration"],
                            "chunk_id": i
                        }],
                        ids=[f"{video_id}_chunk_{i}"]
                    )
                return True
            return False
        except Exception as e:
            st.error(f"Error adding video to knowledge base: {e}")
            return False

    def format_apa_citation(self, metadata: Dict) -> Tuple[str, str]:
        """Format video metadata as APA citation.
        
        Args:
            metadata: Dictionary containing video metadata
            
        Returns:
            Tuple of (full citation, parenthetical citation)
        """
        # Format the date string
        date_str = metadata['upload_date'].strftime("%Y, %B %d")
        year_str = metadata['upload_date'].strftime("%Y")
        
        # Create full citation
        full_citation = (
            f"{metadata['author']}. ({date_str}). "
            f"*{metadata['title']}* [Video]. YouTube. {metadata['url']}"
        )
        
        # Create parenthetical citation
        parenthetical = f"({metadata['author']}, {year_str})"
        
        return full_citation, parenthetical

    def query_video(self, question: str, video_id: Optional[str] = None) -> str:
        """Query the video knowledge base using Mistral, returning summary and quotes."""
        try:
            # Query ChromaDB for relevant chunks
            where_clause = {"video_id": video_id} if video_id else None
            results = self.collection.query(
                query_texts=[question],
                n_results=5,  # Increased to get more context
                where=where_clause
            )
            
            # Get video metadata and format citations
            metadata = self.video_metadata.get(video_id, {
                "title": "Untitled Video",
                "author": "Unknown Author",
                "upload_date": datetime.now(),
                "url": f"https://www.youtube.com/watch?v={video_id}"
            })
            
            full_citation, parenthetical = self.format_apa_citation(metadata)
            
            # Prepare context with timestamps
            context_entries = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                start_time = self.format_timestamp(meta["start_time"])
                end_time = self.format_timestamp(meta["start_time"] + meta["duration"])
                context_entries.append(f"[{start_time}-{end_time}] {doc}")
            
            context = "\n".join(context_entries)
            
            prompt = f"""Based on the following video transcript excerpt, first provide a 1-2 sentence summary, then list the relevant exact quotes with their timestamps.

Video Information:
{full_citation}

Example APA citation format:
Harvard University. (2019, August 28). Soft robotic gripper for jellyfish [Video]. YouTube. https://www.youtube.com/watch?v=guRoWTYfxMs

Transcript context:
{context}

Question: {question}

Required format:
First: Brief summary (1-2 sentences)
Then: Supporting quotes in this format:
"[Complete sentence or statement from transcript]" [MM:SS-MM:SS] {parenthetical}

IMPORTANT:
- Start with a concise summary
- Follow with at least 2-3 relevant quotes if available
- Each quote MUST be a complete sentence or statement
- Ensure quotes include full context and meaning
- Present quotes in chronological order
- Keep quotes verbatim from the transcript
- Do not truncate sentences
- Format citations exactly like the example above"""

            # Get response from Mistral with stronger system prompt
            response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": """You are a precise citation assistant. Your responses must:
1. Begin with a 1-2 sentence summary of the answer
2. Follow with exact quotes from the transcript
3. Include timestamps for every quote
4. Only use complete sentences or statements
5. Present quotes chronologically
6. Format each quote on a new line
7. Never truncate or fragment quotes"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            st.error(f"Error querying video: {e}")
            return "Sorry, I encountered an error while processing your question."

    def process_video_query(self, query: str) -> str:
        """Process a query that contains both a YouTube URL and a question.
        
        Args:
            query (str): Full query containing URL and question
            
        Returns:
            str: Answer based on video content
        """
        try:
            # Extract URL and question from query
            words = query.split()
            video_url = next(word for word in words if any(x in word.lower() 
                for x in ['youtube.com/watch?v=', 'youtu.be/', 'youtube.com/shorts/']))
            
            # Remove the URL from query to get the actual question
            question = query.replace(video_url, '').strip()
            
            # If there's no actual question, return a prompt
            if not question:
                return "What would you like to know about this video?"
            
            # Process video and get answer
            if self.add_video_to_knowledge_base(video_url):
                video_id = self.extract_video_id(video_url)
                return self.query_video(question, video_id)
            return "Sorry, I couldn't process that video. Please make sure it has closed captions available."
            
        except Exception as e:
            st.error(f"Error processing video query: {e}")
            return "Sorry, I encountered an error while processing your request."

    def cleanup(self):
        """Clean up temporary files and close connections."""
        try:
            # Delete the collection
            if hasattr(self, 'collection'):
                self.chroma_client.delete_collection(self.collection.name)
            
            # Close the client
            if hasattr(self, 'chroma_client'):
                del self.chroma_client
            
            # Remove the temporary directory
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            st.error(f"Error during cleanup: {e}") 