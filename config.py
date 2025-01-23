from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

@dataclass
class SnowflakeConfig:
    database: str = os.getenv("SNOWFLAKE_DATABASE", "PROJECTX")
    schema: str = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    search_service: str = os.getenv("SNOWFLAKE_SEARCH_SERVICE", "CC_SEARCH_SERVICE_CS")
    warehouse: str = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    stage_name: str = os.getenv("SNOWFLAKE_STAGE_NAME", "@docs")

@dataclass
class AppConfig:
    available_models: tuple = ("mistral-large-latest")
    default_chunk_size: int = 4000
    default_chunk_overlap: int = 0
    default_search_limit: int = 7
    
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")

APIFY_KEY = os.getenv("APIFY_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENAPI_KEY = os.getenv("OPENAPI_KEY")

CONFIG_LIST = [
    {
        "model": "mistral-large-latest",
        "api_key": MISTRAL_API_KEY,
        "api_type": "mistral"
    },
    {
        "model": "gpt-4o-mini", 
        "api_key": OPENAPI_KEY
    },
]