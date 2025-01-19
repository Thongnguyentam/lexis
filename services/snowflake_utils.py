from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import pandas as pd
import json
from typing import List, Dict, Any
from config import SnowflakeConfig

class SnowflakeConnector:
    def __init__(self, config: SnowflakeConfig):
        self.session = get_active_session()
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

    def search_documents(self, query: str, limit: int) -> pd.DataFrame:
        response = self.search_service.search(
            query=query,
            columns=["CHUNK", "EPISODE_NAME"],
            limit=limit
        ).to_json()
        
        json_data = json.loads(response) if isinstance(response, str) else response
        return pd.json_normalize(json_data['results'])

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
