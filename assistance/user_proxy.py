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
        
        
class IntentClassifier(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="intent_classifier",
            llm_config={"config_list": CONFIG_LIST},
            system_message="""
            Your role is to classify whether to use web search tool:
            If the search result tells that the retrieved documents do not provide direct information about user's message, reply 'yes'. 
            Otherwise, if the documents contains relevant information, reply 'no'. 
            
            Respond with the category 'yes' or 'no' only.
            """
        )
    # - restaurant_reservation: queries requiring to reserve a table at a restaurant
    def classify(self, message: str) -> str:
        # process classification on the intent
        response = self.generate_reply(messages = [{"role": "assistant", "content": message}])
        return response