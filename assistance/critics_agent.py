from autogen import AssistantAgent
from config import CONFIG_LIST
from prompts.critics import CRITIC_DESCRIPTION, CRITIC_MESSAGE

class CriticAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name =  "critic_agent",
            llm_config={"config_list": CONFIG_LIST},
            system_message=CRITIC_MESSAGE,
            description=CRITIC_DESCRIPTION
        )