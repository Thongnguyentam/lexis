from autogen.agentchat.contrib.capabilities.text_compressors import LLMLingua
from autogen.agentchat.contrib.capabilities.transforms import TextMessageCompressor
from autogen.agentchat.contrib.capabilities import transforms, transform_messages
from config import CONFIG_LIST
from autogen import AssistantAgent
from prompts.system_prompts import DEFAULT_ASSISTANT_PROMPT
from prompts.writer_agent import WRITER_DESCRIPTION, WRITER_SYSTEM_MESSAGE

class WriterAgent(AssistantAgent):
    def __init__(self, name="writer_agent"):
        # config list
        self.config_list = CONFIG_LIST
        self.llm_config = {"config_list": CONFIG_LIST}
        
        super().__init__(
            name=name,
            llm_config = self.llm_config,
            system_message=DEFAULT_ASSISTANT_PROMPT,
            description = WRITER_DESCRIPTION,
        )
        self.context_handler = self.add_context_handler()
        self.context_handler.add_to_agent(self)
    
    # configurer the context handler
    def add_context_handler(
        self, 
        target_token= 8192, 
        max_messages=5,
        max_tokens_per_message=8192
    ):
        
        llm_lingua = LLMLingua()
        text_compressor = TextMessageCompressor(
            text_compressor=llm_lingua,
            compression_params={"target_token": target_token},
            #cache=True
        )

        history_limiter = transforms.MessageHistoryLimiter(max_messages=max_messages)
        #token_limiter = transforms.MessageTokenLimiter(model = OPENAI_MODEL,max_tokens=target_token, max_tokens_per_message=max_tokens_per_message)
        context_handling = transform_messages.TransformMessages(
            transforms=[
                text_compressor
            ]
        )
        return context_handling
    
def create_prompt(context: str, message: str):
   prompt = f"""
   Use the context information and relevant documents to answer the question.
   If there is no context information, answer based on your general knowledge. 

   Respond based on the context information provided:
    - If the context information and relevant documents are not sufficient to answer user's message, *ONLY* respond with your general knowledge in any format.
    - If there is relevant information in the context information and relevant documents, *ONLY* respond in this format:
        - Summary: A brief summary of context information and relevant documents.
        - Detailed Analysis: Provide an in-depth and detailed information to answer the question.
        - Source: A list of all referenced sources included in the context information and relevant documents (If applicable).

    <context>
    {context}
    </context>
    <question>  
    {message}
    </question>
   
   Answer: 
   """
   return prompt