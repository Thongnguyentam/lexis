from typing_extensions import Annotated
from autogen import AssistantAgent
from config import CONFIG_LIST, SnowflakeConfig
from prompts.documents_reading_agent import DOCUMENTS_READING_SYSTEM_DESCRIPTION, DOCUMENTS_READING_SYSTEM_MESSAGE
from utils.snowflake_utils import SnowflakeConnector

class DocumentReadingAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="document_reading_agent",
            llm_config={"config_list": CONFIG_LIST},
            description=DOCUMENTS_READING_SYSTEM_MESSAGE,
            system_message = DOCUMENTS_READING_SYSTEM_DESCRIPTION
        )
        self.register_for_llm(name="retrieve_relevant_documents", description="Search relevant documents and return the content and it source.")(retrieve_relevant_documents)
        
    def get_relevant_information(self, message: str):
        search_result = retrieve_relevant_documents(query=message)
        print("search_result", search_result)
        doc_message = f"""
            User's: '{message}'
            Retrieved relevant documents from the databases: {search_result}\n

            *ONLY* Respond in this format:
            1. *Summary*: A brief summary of the findings from the database, explicitly referencing the sources.
            2. *Detailed Analysis*: An in-depth explanation based on the documents, with citations for each piece of information.
            3. *Citations*: A list of all referenced sources included in the relative path of the search results.

            Example Response:
            - *Summary*: Key insights from the documents include X, Y, and Z (sourced from 'relative_path_to_document.pdf').
            - *Detailed Analysis*: The document 'relative_path_to_document.pdf' highlights that [detailed analysis of X]. Additionally, 'another_document.pdf' explains [detailed analysis of Y]. 
            - *Citations*: 
            1. relative_path_to_document.pdf
            2. another_document.pdf
            """
        response = self.generate_reply(messages = [{"role": "assistant", "content": doc_message}])
        return response
        
def retrieve_relevant_documents(query: Annotated[str, "Search query for relevant documents"]) -> Annotated[str, "Search results"]:
    """
    Perform a retrieval-augmented search on the Snowflake database. This function utilizes the Retrieval-Augmented Generation (RAG) approach to search 
    for relevant documents in the Snowflake database. It retrieves document chunks similar to the provided query.

    :param query: str
        The search query used to retrieve relevant documents. This should be a descriptive 
        query or keyword relevant to the content of uploaded documents.
    :return: str
        The search results, including chunks of relevant text and metadata matching 
        the query.
    """
    snowflake_config = SnowflakeConfig()
    snowflake_conn = SnowflakeConnector(snowflake_config)
    return snowflake_conn.get_similar_chunks_search_service(query=query)