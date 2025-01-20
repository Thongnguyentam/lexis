from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import pandas as pd
import json
from typing import List, Dict, Any
from config import SNOWFLAKE_ACCOUNT, SNOWFLAKE_DATABASE, SNOWFLAKE_PASSWORD, SNOWFLAKE_SCHEMA, SNOWFLAKE_USER, SNOWFLAKE_WAREHOUSE, SnowflakeConfig
from snowflake.snowpark import Session
import os
from dotenv import load_dotenv

class SnowflakeConnector:
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
        
        return response.model_dump_json()  

    # check
    def create_prompt(self, query:str):
        prompt_context = self.get_similar_chunks_search_service(query)
  
        prompt = f"""
           You are an expert chat assistance that extracs information from the CONTEXT provided
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

        json_data = json.loads(prompt_context)
        relative_paths = set(item['relative_path'] for item in json_data['results'])
        
        return prompt, relative_paths
        
    def generate_response(self, model: str, prompt: str, context: str) -> str:
        query = f"""
        SELECT snowflake.cortex.complete(
            '{model}',
            CONCAT(
                'Answer the question ONLY using the context provided. Context: ',
                '{context}',
                'Question: ',
                '{prompt}',
                'Answer: '
            )
        ) as response
        """
        result = self.session.sql(query).collect()
        return result[0]['RESPONSE']

#check
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
        print("Connection Parameters (excluding password):")
        print(f"Account: {account}")
        print(f"User: {user}")
        print(f"Database: {database}")
        print(f"Schema: {schema}")
        print(f"Warehouse: {warehouse}")
        
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