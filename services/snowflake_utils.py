from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import pandas as pd
import json
from typing import List, Dict, Any
from config import SNOWFLAKE_ACCOUNT, SNOWFLAKE_DATABASE, SNOWFLAKE_PASSWORD, SNOWFLAKE_SCHEMA, SNOWFLAKE_USER, SNOWFLAKE_WAREHOUSE, SnowflakeConfig
from snowflake.snowpark import Session

class SnowflakeConnector:
    # check
    def __init__(self, config: SnowflakeConfig):
        self.session = get_snowpark_session()
        self.config = config
        self.root = Root(self.session)
        self.search_service = (
            self.root
            .databases[self.config.database]
            .schemas[self.config.schema]
            .cortex_search_services[self.config.search_service]
        )

    def parse_documents_to_table(self, target_table: str) -> None:
        query = f"""
        CREATE OR REPLACE TABLE {target_table} AS
        SELECT
            relative_path as episode_name,
            file_url,
            TO_VARCHAR(
                SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
                    '{self.config.stage_name}',
                    relative_path,
                    {{'mode': 'LAYOUT'}}
                ):content
            ) AS raw_text
        FROM directory({self.config.stage_name});
        """
        self.session.sql(query).collect()
        
    def count_tokens(self, text_column: str, table_name: str) -> int:
        """Count tokens in the parsed text."""
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COUNT_TOKENS('summarize', {text_column})
        FROM {table_name}
        LIMIT 1;
        """
        result = self.session.sql(query).collect()
        return result[0][0]
        
    def create_chunked_table(self, table_name: str, source_table: str, chunk_size: int, overlap: int) -> None:
        query = f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT
            episode_name,
            TO_VARCHAR(c.value) as chunk
        FROM {source_table},
        LATERAL FLATTEN(
            input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
                raw_text,
                'markdown',
                {chunk_size},
                {overlap}
            )
        ) c;
        """
        self.session.sql(query).collect()
    
    def create_search_service(self, service_name: str, source_table: str) -> None:
        query = f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {service_name}
        ON CHUNK
        ATTRIBUTES EPISODE_NAME
        WAREHOUSE = {self.config.warehouse}
        TARGET_LAG = '7 days'
        AS (
            SELECT CHUNK, EPISODE_NAME
            FROM {source_table}
        );
        """
        self.session.sql(query).collect()

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
    """ Get or create a Snowpark session """
    connection_parameters = {
            "account": SNOWFLAKE_ACCOUNT,
            "user": SNOWFLAKE_USER,
            "password": SNOWFLAKE_PASSWORD,
            "warehouse": SNOWFLAKE_WAREHOUSE,
            "database": SNOWFLAKE_DATABASE,
            "schema": SNOWFLAKE_SCHEMA
        }
    return Session.builder.configs(connection_parameters).create()