from snowflake.snowpark.session import Session
from snowflake.snowpark.functions import udf
import json
import pandas as pd
from typing import List, Dict, Any
import os
from mistralai import Mistral

class SnowflakeRAG:
    def __init__(self, warehouse: str = "tc_wh"):
        # Initialize Snowflake session using connection parameters
        self.session = Session.builder.configs({
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "warehouse": warehouse,
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA")
        }).create()
        
        # Initialize Mistral client
        self.mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        
    def extract_pdf_text(self, stage_path: str, table_name: str) -> None:
        """Extract text from PDFs in the specified stage"""
        try:
            query = f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT
                relative_path as document_name,
                file_url,
                SYSTEM$PARSE_DOCUMENT(
                    build_scoped_file_url('{stage_path}', relative_path),
                    'PDF'
                ) AS raw_text
            FROM directory({stage_path});
            """
            self.session.sql(query).collect()
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")

    def chunk_text(self, source_table: str, target_table: str, chunk_size: int = 4000) -> None:
        """Chunk extracted text into smaller segments"""
        try:
            query = f"""
            CREATE OR REPLACE TABLE {target_table} AS
            WITH split_text AS (
                SELECT 
                    document_name,
                    REGEXP_SPLIT_TO_TABLE(
                        raw_text,
                        '(?<=\\. )|(?<=\\n)',
                        {chunk_size}
                    ) as chunk
                FROM {source_table}
            )
            SELECT 
                document_name,
                chunk
            FROM split_text
            WHERE LENGTH(chunk) > 0;
            """
            self.session.sql(query).collect()
        except Exception as e:
            raise Exception(f"Error chunking text: {str(e)}")

    def create_vector_search(self, table_name: str) -> None:
        """Create vector search index"""
        try:
            # First create embeddings column
            query = f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS embedding VECTOR;
            
            UPDATE {table_name}
            SET embedding = SYSTEM$EMBED_TEXT(chunk)
            WHERE embedding IS NULL;
            
            CREATE OR REPLACE SEARCH OPTIMIZATION ON {table_name}
            WITH PARAMETERS (
                optimization_type = 'VECTOR_SEARCH',
                vector_column = 'EMBEDDING'
            );
            """
            self.session.sql(query).collect()
        except Exception as e:
            raise Exception(f"Error creating vector search: {str(e)}")

    def search_context(self, table_name: str, query: str, limit: int = 3) -> Dict[str, Any]:
        """Search for relevant context using vector similarity"""
        try:
            search_query = f"""
            SELECT 
                document_name,
                chunk,
                vector_cosine_similarity(
                    SYSTEM$EMBED_TEXT(:query),
                    embedding
                ) as similarity
            FROM {table_name}
            ORDER BY similarity DESC
            LIMIT {limit}
            """
            result = self.session.sql(search_query)\
                .bind_parameter('query', query)\
                .to_pandas()
            return {
                "results": result.to_dict('records')
            }
        except Exception as e:
            raise Exception(f"Error searching context: {str(e)}")

    def get_llm_response(self, prompt: str, context: Dict[str, Any], model_name: str = "mistral-large-latest") -> str:
        """Generate LLM response using retrieved context"""
        try:
            system_prompt = f'''
            Answer the question ONLY using the context provided. Here is the context to use:
            ### Context:
            {context}
            ### Question:
            {prompt}
            '''
            
            response = self.mistral_client.chat.complete(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating LLM response: {str(e)}")

    def close(self):
        """Close the Snowflake session"""
        if self.session:
            self.session.close() 