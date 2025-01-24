from snowflake.core import Root
import pandas as pd
import json
from typing import List, Dict, Any
from assistance.critics_agent import CriticAgent, reflection_message
from assistance.documents_reading_agent import DocumentReadingAgent
from assistance.intent_classifier_agent import IntentClassifier
from assistance.paper_search_agent import PaperSearchAgent
from assistance.user_proxy import UserProxy
from assistance.web_search_agent import WebSearchAgent
from assistance.writer_agent import WriterAgent, create_prompt
from config import SNOWFLAKE_ACCOUNT, SNOWFLAKE_DATABASE, SNOWFLAKE_PASSWORD, SNOWFLAKE_SCHEMA, SNOWFLAKE_USER, SNOWFLAKE_WAREHOUSE, SnowflakeConfig
from snowflake.snowpark import Session
import os
from dotenv import load_dotenv

from services.search_service import generate_request_to_recipient
from trulens.apps.custom import instrument
from trulens.core.guardrails.base import context_filter

class AgentRAG:
    def __init__(self, config: SnowflakeConfig):
        try:
            # Store config first before any other operations
            self.config = config
            
            # Validate config
            if not all([
                self.config.database,
                self.config.schema,
                self.config.search_service,
                self.config.warehouse
            ]):
                raise ValueError(
                    "Invalid configuration. Please check your environment variables:\n"
                    f"Database: {self.config.database}\n"
                    f"Schema: {self.config.schema}\n"
                    f"Search Service: {self.config.search_service}\n"
                    f"Warehouse: {self.config.warehouse}"
                )
            
            # Then initialize session
            self.session = get_snowpark_session()
            self.root = Root(self.session)
            
            # Verify search service exists
            if not hasattr(self.root.databases[self.config.database].schemas[self.config.schema], 'cortex_search_services'):
                raise ValueError(f"No search services found in {self.config.database}.{self.config.schema}")
            
            self.search_service = (
                self.root
                .databases[self.config.database]
                .schemas[self.config.schema]
                .cortex_search_services[self.config.search_service]
            )
            
            print(f"Successfully initialized SnowflakeConnector with search service: {self.config.search_service}")
            
        except Exception as e:
            if hasattr(self, 'config'):
                detailed_error = f"Snowflake initialization failed:\n" \
                               f"Database: {self.config.database}\n" \
                               f"Schema: {self.config.schema}\n" \
                               f"Search Service: {self.config.search_service}\n" \
                               f"Error: {str(e)}"
            else:
                detailed_error = f"Snowflake initialization failed before config could be set: {str(e)}"
            print(f"Error: {detailed_error}")  # Debug print
            raise Exception(detailed_error)

    #check
    def get_similar_chunks_search_service(
        self, 
        query, 
        category_value: str = "ALL", 
        columns: List[str] = ["chunk", "relative_path", "category"], 
        num_chunks: int = 3
    ):
        if category_value == "ALL":
            response = self.search_service.search(query, columns, limit=num_chunks)
        else: 
            filter_obj = {"@eq": {"category": category_value} }
            response = self.search_service.search(query, columns, filter=filter_obj, limit=num_chunks)
        
        return response.results
    
    # new
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        #intent classification
        intent_agent = IntentClassifier()
        paper_search_agent=PaperSearchAgent()
        web_search_agent = WebSearchAgent()
        document_reading_agent = DocumentReadingAgent()
        intent = intent_agent.classify(query)
        #print(intent)
        
        if 'papers_search' in intent:
            search_res = paper_search_agent.search_paper(query=query)
            if not search_res or (search_res == "" or "no info" in search_res):
                search_res = ""
        elif 'web_search' in intent:
            # always use tools to search
            search_res = web_search_agent.search_web(query=query)
            if not search_res or (search_res == "" or "no info" in search_res):
                search_res = ""
        else:
            search_res = ""
        #print(f"search_res: {search_res}")
        
        # For all intents that require reading a document from the RAG 
        relev_doc = self.get_similar_chunks_search_service(query=query)
        relevant_chunks = document_reading_agent.get_relevant_information(message=query, retrieve_relevant_documents=relev_doc)
        if not relevant_chunks or (relevant_chunks == "" or "no info" in relevant_chunks):
            relevant_chunks = ""
        #print(f"relev_doc: {relevant_chunks}")

        context = f"""       
        {search_res} \n
        {relevant_chunks} \n
        """
        return context.strip()
        
    # new generate function using agents
    @instrument
    def generate_completion(self, query: str, context_str: list) -> str:
        user_proxy = UserProxy()
        critic_agent = CriticAgent()
        writer_agent = WriterAgent()
        
        user_proxy.register_nested_chats(
            chat_queue= [
                {
                    "recipient": critic_agent, 
                    "clear_history": True,
                    "message": reflection_message,
                    "summary_method": "last_msg", 
                    "max_turns": 1
                }
                ],
            trigger=writer_agent
        )
        aggregate_prompt = create_prompt(context=context_str, message=query)
        chat_queue = []
        chat_queue.append(generate_request_to_recipient(agent=writer_agent,message=aggregate_prompt, max_turns=2))
        res = user_proxy.initiate_chats(chat_queue=chat_queue)
        return res[-1].chat_history[-1]['content']
    
    # new
    @instrument 
    def query(self, query: str) -> str:
        context_str = self.retrieve(query)
        completion = self.generate_completion(query, context_str)
        return completion
 
class FilteredAgentRAG(AgentRAG):
    def __init__(self, config: SnowflakeConfig):
        super().__init__(config)
        
    @context_filter(f_guardrail, 0.75, keyword_for_prompt="query")
    def get_similar_chunks_search_service(
        self, 
        query, 
        category_value: str = "ALL", 
        columns: List[str] = ["chunk", "relative_path", "category"], 
        num_chunks: int = 3
    ):
        if category_value == "ALL":
            response = self.search_service.search(query, columns, limit=num_chunks)
        else: 
            filter_obj = {"@eq": {"category": category_value} }
            response = self.search_service.search(query, columns, filter=filter_obj, limit=num_chunks)
        
        return response.results

def get_snowpark_session():
    """Get or create a Snowpark session"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get connection parameters
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        user = os.getenv("SNOWFLAKE_USER")
        password = os.getenv("SNOWFLAKE_PASSWORD")
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        database = os.getenv("SNOWFLAKE_DATABASE")
        schema = os.getenv("SNOWFLAKE_SCHEMA")
        
        # Debug print (will be removed in production)
        # print("Connection Parameters (excluding password):")
        # print(f"Account: {account}")
        # print(f"User: {user}")
        # print(f"Database: {database}")
        # print(f"Schema: {schema}")
        # print(f"Warehouse: {warehouse}")
        
        # Verify all required parameters are present
        if not all([account, user, password, warehouse, database, schema]):
            missing = [
                param for param, value in {
                    "SNOWFLAKE_ACCOUNT": account,
                    "SNOWFLAKE_USER": user,
                    "SNOWFLAKE_PASSWORD": password,
                    "SNOWFLAKE_WAREHOUSE": warehouse,
                    "SNOWFLAKE_DATABASE": database,
                    "SNOWFLAKE_SCHEMA": schema
                }.items() if not value
            ]
            raise ValueError(f"Missing required Snowflake parameters: {', '.join(missing)}")
        
        # Create connection parameters
        connection_parameters = {
            "account": account,
            "user": user,
            "password": password,
            "warehouse": warehouse,
            "database": database,
            "schema": schema
        }
        
        # Try to create session
        session = Session.builder.configs(connection_parameters).create()
        print("Snowflake session created successfully!")
        return session
        
    except Exception as e:
        error_msg = f"Failed to create Snowpark session: {str(e)}"
        print(f"Error: {error_msg}")  # Debug print
        raise Exception(error_msg)