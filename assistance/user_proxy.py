from autogen import AssistantAgent, UserProxyAgent
from assistance.documents_reading_agent import retrieve_relevant_documents
from assistance.web_search_agent import search_internet
from config import CONFIG_LIST
from prompts.user_proxy import USER_PROXY_SYSTEM_MESSAGE
class UserProxy(UserProxyAgent):
    def __init__(self):
        super().__init__(
            name="user_proxy",
            human_input_mode="NEVER",
            llm_config=False, # add here
            is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
            system_message = USER_PROXY_SYSTEM_MESSAGE,
            default_auto_reply="Please continue if not finished, otherwise return 'TERMINATE'." # add here
        )
        self.register_for_execution(name="search_internet")(search_internet)
        self.register_for_execution(name="retrieve_relevant_documents")(retrieve_relevant_documents)
        