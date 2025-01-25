from snowflake.core import Root

from typing import List
from config import MISTRAL_API_KEY, SNOWFLAKE_ACCOUNT, SNOWFLAKE_DATABASE, SNOWFLAKE_PASSWORD, SNOWFLAKE_SCHEMA, SNOWFLAKE_USER, SNOWFLAKE_WAREHOUSE, SnowflakeConfig

import os
from dotenv import load_dotenv
load_dotenv()
from prompts.system_prompts import DEFAULT_ASSISTANT_PROMPT
from services.rag_agents import get_snowpark_session
from trulens.apps.custom import instrument
from mistralai import Mistral

class NoAgentRAG:
    def __init__(self, config: SnowflakeConfig):
        try:
            # Initialize Mistral client
            api_key = MISTRAL_API_KEY
            if not api_key:
                # Instead of raising an error, just set client to None
                self.mistral_client = None
                return
            self.mistral_client = Mistral(api_key=api_key)
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
    
    def create_prompt(self, query:str, prompt_context:list) -> str:  
        prompt = f"""
           You are an expert chat assistance that extracts information from the CONTEXT provided
           between <context> and </context> tags.
           When ansering the question contained between <question> and </question> tags
           be concise and do not hallucinate. 
           If you don´t have the information just say so.
           Only anwer the question if you can extract it from the CONTEXT provideed.
           
           Do not mention the CONTEXT used in your answer.
    
           <context>          
           {prompt_context}
           </context>
           <question>  
           {query}
           </question>
           Answer: 
           """

        relative_paths = set(item['relative_path'] for item in prompt_context)
        
        return prompt, relative_paths
    
    @instrument
    def retrieve(self, query:str) -> str:
        return self.get_similar_chunks_search_service(query)
    
    @instrument
    def generate_completion(self, query:str, context_str: list) -> str:
        # Get RAG context and prompt
        prompt, source_paths = self.create_prompt(query, context_str)
        # Use Mistral with RAG context
        response = self.mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": DEFAULT_ASSISTANT_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Add source attribution if sources were found
        answer = response.choices[0].message.content
        if source_paths:
            sources_list = "\n".join([f"- {path}" for path in source_paths])
            answer += f"\n\nSources:\n{sources_list}"
        return answer
    
    @instrument
    def query(self, query: str) -> str:
        context_str = self.retrieve(query)
        completion = self.generate_completion(query, context_str)
        return completion