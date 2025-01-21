from datetime import datetime
import json
import re

from assistance.critics_agent import CriticAgent
from assistance.documents_reading_agent import DocumentReadingAgent
from assistance.user_proxy import UserProxy
from assistance.web_search_agent import WebSearchAgent
from assistance.writer_agent import WriterAgent
from prompts.critics import REFLECTION_MESSAGE

def create_prompt(context: str, message: str):
   prompt = f"""
   Use the following pieces of retrieved context to answer the message.
   If you don´t have the information just say so and suggest from your general knowledge.
   ** DO NOT ** include sources that do not contain information about the user's message. 

   **ONLY** respond in this format:
   1. Summary: A brief summary of the findings from the database, explicitly referencing the sources.
   2. Detailed Analysis: An in-depth explanation based on the documents, with citations for each piece of information.
   3. Citations: A list of all referenced sources included in the relative path of the search results (If applicable).

   <context>          
   {context}
   </context>
   <question>  
   {message}
   </question>
   Answer: 
   """
   return prompt

def create_web_search_prompt(search_res: str, message:str):
    return f"""
        User's message: '{message}'
        Search Result: {search_res}
        
        If there is no search result, or the search result tells that the retrieved documents is not sufficient or do not provide direct information about user's message, reply 'yes'. 
        Otherwise, if the documents contains relevant information or sufficient information to answer user's message, reply 'no'. 
        
        **ONLY** Respond 'yes' or 'no'.
    """

def reflection_message(recipient, messages, sender, config):
        print(f"Critic Agent Reflecting ...", "yellow")
        message = REFLECTION_MESSAGE
        last_message = recipient.chat_messages_for_summary(sender)[-1]['content']
        user_said = recipient.chat_messages_for_summary(sender)[0]['content']
        match = re.search(r"User:\s\"(.*?)\"", user_said)
        if match:
            user_said = match.group(1)
            
        return f"""
        Researcher's response: \n{last_message} \n
        {message} \n
        User: {user_said} \n
        
        """
        
def generate_request_to_recipient(
    agent,
    message: str,
    clear_history: bool = True,
    summary_method: str = "last_msg",
    max_turns: int = 1,
    carry_over: str = None,
):
    return {
            "recipient": agent, 
            "message": message, 
            "clear_history": clear_history, 
            "carry_over": carry_over,
            "summary_method": summary_method, 
            "max_turns": max_turns
        }
    
def search(message: str):
    #agents initialization
    user_proxy = UserProxy()
    web_search_agent = WebSearchAgent()
    writer_agent = WriterAgent()
    critic_agent = CriticAgent()
    document_reading_agent = DocumentReadingAgent()
    web_search_intent = IntentClassifier()

    # Sequential chat configuration
    user_proxy.register_nested_chats(
        chat_queue= [
            {
                "recipient": critic_agent, 
                "clear_history": True,
                "message": reflection_message,
                "summary_method": "last_msg", 
                "max_turns": 1
            }
            ],
        trigger=writer_agent
    )
    
    search_res = document_reading_agent.get_relevant_information(message=message)
    if search_res and (search_res == "" or "no info" in search_res):
        search_res = "no related documents found"
        
    web_search_prompt = create_web_search_prompt(search_res=search_res, message=message)
    is_search = web_search_intent.classify(web_search_prompt)
    print("is_search: ", is_search)
    chat_queue = []
    if is_search and 'yes' in is_search:
        chat_queue.append(generate_request_to_recipient(agent=web_search_agent, message= message, max_turns=2, summary_method="reflection_with_llm"))
    aggregate_prompt = create_prompt(context=search_res, message=message)
    chat_queue.append(generate_request_to_recipient(agent=writer_agent,message=aggregate_prompt, max_turns=2))

    res = user_proxy.initiate_chats(chat_queue=chat_queue)
    return res[-1].chat_history[-1]['content'] 