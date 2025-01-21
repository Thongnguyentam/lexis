from config import CONFIG_LIST
from autogen import AssistantAgent

class IntentClassifier(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="intent_classifier",
            llm_config={"config_list": CONFIG_LIST},
            system_message="""    
            Your role is to classify user intents into one of these categories:
            - uploaded_document_read: queries requiring retrieved user's uploaded documents to answer questions
            - papers_search: quieries requiring searching for papers on axvir or web 
            - web_search: queries requiring real-time online search on the web
            - general: General queries that don't fit the above categories
            
            Respond with the category name only.
            """
        )
        
    def classify(self, message: str) -> str:
        # process classification on the intent
        response = self.generate_reply(messages = [{"role": "assistant", "content": message}])
        return response['content']
    