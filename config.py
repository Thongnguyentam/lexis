from dataclasses import dataclass
import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

@dataclass
class SnowflakeConfig:
    database: str = st.secrets["env"]["SNOWFLAKE_DATABASE"]
    schema: str = st.secrets["env"]["SNOWFLAKE_SCHEMA"]
    search_service: str = st.secrets["env"]["SNOWFLAKE_SEARCH_SERVICE"]
    warehouse: str = st.secrets["env"]["SNOWFLAKE_WAREHOUSE"]
    stage_name: str = st.secrets["env"]["SNOWFLAKE_STAGE_NAME"]

@dataclass
class AppConfig:
    available_models: tuple = ("mistral-large-latest")
    default_chunk_size: int = 4000
    default_chunk_overlap: int = 0
    default_search_limit: int = 7
    
SNOWFLAKE_ACCOUNT = st.secrets["env"]["SNOWFLAKE_ACCOUNT"]
SNOWFLAKE_USER = st.secrets["env"]["SNOWFLAKE_USER"]
SNOWFLAKE_PASSWORD = st.secrets["env"]["SNOWFLAKE_PASSWORD"]
SNOWFLAKE_DATABASE = st.secrets["env"]["SNOWFLAKE_DATABASE"]
SNOWFLAKE_SCHEMA = st.secrets["env"]["SNOWFLAKE_SCHEMA"]
SNOWFLAKE_WAREHOUSE = st.secrets["env"]["SNOWFLAKE_WAREHOUSE"]
SNOWFLAKE_SEARCH_SERVICE = st.secrets["env"]["SNOWFLAKE_SEARCH_SERVICE"]
SNOWFLAKE_STAGE_NAME = st.secrets["env"]["SNOWFLAKE_STAGE_NAME"]

APIFY_KEY = st.secrets["env"]["APIFY_KEY"]
MISTRAL_API_KEY = st.secrets["env"]["MISTRAL_API_KEY"]
OPENAPI_KEY = st.secrets["env"]["OPENAI_API_KEY"]

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