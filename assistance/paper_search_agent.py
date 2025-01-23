import arxiv
from typing_extensions import Annotated
from autogen import AssistantAgent

from config import CONFIG_LIST
from prompts.paper_search_agent import PAPERS_SEARCH_DESCRIPTION, PAPERS_SEARCH_SYSTEM_MESSAGE

class PaperSearchAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="paper_search_agent",
            llm_config={"config_list": CONFIG_LIST},
            description= PAPERS_SEARCH_SYSTEM_MESSAGE,
            system_message = PAPERS_SEARCH_DESCRIPTION
        )
        
        self.register_for_llm(name="fetch_arxiv_papers", description=(
            "Performs a search for papers and articles on Arxiv database using the arxiv package."
            "The function search papers and returns their summary and sources."
        ))(fetch_arxiv_papers)
    
    def search_paper(self, query: str):
        search_keywords_prompt = f"""
            -------- TASK --------
            - Generate a list of search keywords to find relevant papers or articles that can answer the given query using the Arxiv database.
            - If the query explicitly references a specific paper title, include its title or identifier as a keyword.
            - For general queries, identify the most important terms and related concepts.
            - Ensure the keywords are directly relevant to the query topic and formatted as a comma-separated list.
            - DO NOT answer the query, respond with the keywords only.
            
            -------- FORMAT --------
            - 'keyword1, keyword2, keyword3, ...'
            
            -------- SAMPLES --------
            1.
            Query: 'What is the paper 1605.08386 about?'
            Answer: '1605.08386'
            
            Explanation: The keyword can be '1605.08386' since it is the identifier of the paper.
            --------------------
            
            2.
            Query: "what is Retrieval-Augmented Generation for Large Language Models: A Survey about?"
            Answer: 'Retrieval-Augmented Generation, Large Language Models, Survey'
            
            Explanation: The keywords can be 'Retrieval-Augmented Generation, Large Language Models, Survey' as these are relevant to the topic of the query.
            --------------------
            
            3.
            Query: "what is Retrieval-Augmented Generation for Large Language Models: A Survey article about?"
            Answer: Retrieval-Augmented Generation for Large Language Models: A Survey
            
            Explanation: The keywords can be 'Retrieval-Augmented Generation, Large Language Models, Survey' since it might be the article's title.
            --------------------
            
            4.
            Query: "what is 'Retrieval-Augmented Generation for Large Language Models: A Survey' article about?"
            Answer: Retrieval-Augmented Generation for Large Language Models: A Survey
            
            Explanation: The keywords can be 'Retrieval-Augmented Generation, Large Language Models, Survey' since it might be the article's title.
            
            --------------------
            
            5.
            Query: "Find me a paper about the application of deep learning in material science"
            Answer: 'deep learning, material science, machine learning, materials informatics, computational materials'
            
            Explanation: These keywords capture the essence of the query and broaden its scope with related terms.
            --------------------
            
            -------- INPUT --------
            Query: '{query}'
            Answer:
        """
        keywords = self.generate_reply(messages = [{"role": "user", "content": search_keywords_prompt}])
        keywords = keywords['content']
        keywords = keywords.split(",")
        print("keywords: ", keywords)
        papers = []
        for i in range(min(5, len(keywords))):
            keyword = keywords[i].strip()
            papers.append(fetch_arxiv_papers(title=keyword, papers_count=5))
        print("paper result: ", papers)
        paper_prompt = f"""
            Available papers are below.\n
            ---------------------\n
            {papers}
            ---------------------\n
            - Provide relevant papers that can be used to answer the query.
            - For each of the paper, provide its title, summary, and url.
            
            Query: '{query}'
            Answer:
        """
        response = self.generate_reply(messages = [{"role": "assistant", "content": paper_prompt}])
        response = response['content']
        return response
        
def fetch_arxiv_papers(
    title: Annotated[str, "title or search keyword for the relevant papers or articles"], 
    papers_count: Annotated[int, "Number of papers to fetch"] = 10
) -> Annotated[list, "List of papers"]:
    """
    Search Papers Tool
    Arxiv Tool
    Search Papers Tool for arXiv
    Performs a search for papers and articles on Arxiv database using the arxiv package.

    :param title: str, search keyword for the relevant papers or articles.
    :param papers_count: int, number of papers to fetch.
    :return: list, search results.
    """
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9\s\.]', ' ', title) # Keep alphanumeric, spaces, and some safe characters
    cleaned = re.sub(r'\s+', ' ', cleaned) # Replace multiple spaces with single space
    cleaned = cleaned.strip()
    terms = cleaned.split()
    query_terms = f'("{" AND ".join(terms)}")'
    search_query = f'all:"{query_terms}"'
    search = arxiv.Search(
        query=search_query,
        max_results=papers_count,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    papers = []
    # Use the Client for searching
    client = arxiv.Client()
    
    # Execute the search
    search = client.results(search)

    for result in search:
        paper_info = {
                'title': result.title,
                'summary': result.summary,
                'pdf_url': result.pdf_url
            }
        papers.append(paper_info)

    return papers