from dataclasses import dataclass

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