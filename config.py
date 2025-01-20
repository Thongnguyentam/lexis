from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

@dataclass
class SnowflakeConfig:
    database: str = "LLM_DEMO"
    schema: str = "PODCASTS"
    search_service: str = "NEW_HUBERMAN"
    warehouse: str = "tc_wh"
    stage_name: str = "@huberman"

@dataclass
class AppConfig:
    available_models: tuple = ("mistral-large2", "mistral-7b", "llama3.1-8b")
    default_chunk_size: int = 4000
    default_chunk_overlap: int = 0
    default_search_limit: int = 7
    
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")