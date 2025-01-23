from assistance.critics_agent import CriticAgent, reflection_message
from assistance.documents_reading_agent import DocumentReadingAgent
from assistance.intent_classifier_agent import IntentClassifier
from assistance.paper_search_agent import PaperSearchAgent
from assistance.user_proxy import UserProxy
from assistance.web_search_agent import WebSearchAgent
from assistance.writer_agent import WriterAgent, create_prompt
        
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
    web_search_agent = WebSearchAgent()
    document_reading_agent = DocumentReadingAgent()
    intent_agent = IntentClassifier()
    paper_search_agent=PaperSearchAgent()
    user_proxy = UserProxy()
    critic_agent = CriticAgent()
    writer_agent = WriterAgent()

    #intent classification
    intent = intent_agent.classify(message)
    print(intent)
    
    if 'papers_search' in intent:
        search_res = paper_search_agent.search_paper(query=message)
        if not search_res or (search_res == "" or "no info" in search_res):
            search_res = "no related information found"
    elif 'web_search' in intent:
        # always use tools to search
        search_res = web_search_agent.search_web(query=message)
        if not search_res or (search_res == "" or "no info" in search_res):
            search_res = "no related information found"
    else:
        search_res = "no related information found"
    print(f"search_res: {search_res}")
    
    # For all intents that require reading a document from the RAG 
    relev_doc = document_reading_agent.get_relevant_information(message=message)
    if not relev_doc or (relev_doc == "" or "no info" in relev_doc):
        relev_doc = "no related documents found"
    print(f"relev_doc: {relev_doc}")
    
    aggregate_prompt = create_prompt(context=search_res, relev_doc= relev_doc, message=message)
    
    # Nested chat configuration
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

    chat_queue = []
    chat_queue.append(generate_request_to_recipient(agent=writer_agent,message=aggregate_prompt, max_turns=2))
    res = user_proxy.initiate_chats(chat_queue=chat_queue)
    return res[-1].chat_history[-1]['content']