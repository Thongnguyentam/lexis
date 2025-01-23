import re
from autogen import AssistantAgent
from config import CONFIG_LIST
from prompts.critics import CRITIC_DESCRIPTION, CRITIC_MESSAGE, REFLECTION_MESSAGE

class CriticAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name =  "critic_agent",
            llm_config={"config_list": CONFIG_LIST},
            system_message=CRITIC_MESSAGE,
            description=CRITIC_DESCRIPTION
        )
        
def reflection_message(recipient, messages, sender, config):
        print(f"Critic Agent Reflecting ...", "yellow")
        message = REFLECTION_MESSAGE
        last_message = recipient.chat_messages_for_summary(sender)[-1]['content']
        user_said = recipient.chat_messages_for_summary(sender)[0]['content']
        match = re.search(r"User:\s\"(.*?)\"", user_said)
        if match:
            user_said = match.group(1)
            
        return f"""
        <researcher's response> \n{last_message} \n <researcher's response>
        {message} \n
        <user's message> \n{user_said}\n </user's message>
        """