from typing_extensions import Annotated
from autogen import AssistantAgent
from config import CONFIG_LIST, SnowflakeConfig
from prompts.documents_reading_agent import DOCUMENTS_READING_SYSTEM_DESCRIPTION, DOCUMENTS_READING_SYSTEM_MESSAGE

class DocumentReadingAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="document_reading_agent",
            llm_config={"config_list": CONFIG_LIST},
            description=DOCUMENTS_READING_SYSTEM_MESSAGE,
            system_message = DOCUMENTS_READING_SYSTEM_DESCRIPTION
        )
        
    def get_relevant_information(self, message: str, retrieve_relevant_documents: Annotated[list, "Search results"]) -> str:
        doc_message = f"""
            User's: '{message}'
            Retrieved relevant documents: {retrieve_relevant_documents}\n

            - Extract only information that can be used to answer user's message and its corresponding source file names
            - Ensure the extracted information is complete, accurate, standalone that can be uderstood without the context
            - Do not hallucinate
            - Do not answer user's message, respond with the extracted information only
            
            """
        response = self.generate_reply(messages = [{"role": "assistant", "content": doc_message}])
        response = response['content']
        return response
        
# def retrieve_relevant_documents(query: Annotated[str, "Search query for relevant documents"]) -> Annotated[str, "Search results"]:
#     """
#     Perform a retrieval-augmented search on the Snowflake database. This function utilizes the Retrieval-Augmented Generation (RAG) approach to search 
#     for relevant documents in the Snowflake database. It retrieves document chunks similar to the provided query.

#     :param query: str
#         The search query used to retrieve relevant documents. This should be a descriptive 
#         query or keyword relevant to the content of uploaded documents.
#     :return: str
#         The search results, including chunks of relevant text and metadata matching 
#         the query.
#     """
#     snowflake_config = SnowflakeConfig()
#     snowflake_conn = SnowflakeRAG(snowflake_config)
#     return snowflake_conn.get_similar_chunks_search_service(query=query)