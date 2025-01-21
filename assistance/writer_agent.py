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