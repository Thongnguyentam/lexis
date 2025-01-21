from autogen import AssistantAgent
from typing_extensions import Annotated
from duckduckgo_search import DDGS
import random
from config import APIFY_KEY, CONFIG_LIST
from prompts.web_search_agent import WEB_SEARCH_DESCRIPTION, WEB_SEARCH_SYSTEM_MESSAGE
from utils.custom_actor_client import CustomApifyClient
from autogen import AssistantAgent
from datetime import datetime
import arxiv
class WebSearchAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name =  "web_search_agent",
            llm_config={"config_list": CONFIG_LIST},
            system_message=WEB_SEARCH_SYSTEM_MESSAGE,
            description=WEB_SEARCH_DESCRIPTION
        )
    
        self.register_for_llm(name="search_internet", description=(
                "Perform a web search to find relevant content if there is no sufficient information in the context for answering the question. "
                "The function scrapes the web page and returns the content with sources."
            ))(search_internet)

def get_headers() -> dict:
    """Generate random headers"""
    user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/"
    }
    
def scrape_page(urls: list[Annotated[str, "The URL of the web page to scrape"]]) -> Annotated[dict, "Scraped content"]:
    # Initialize the ApifyClient with your API token
        
    client = CustomApifyClient(token=APIFY_KEY, headers=get_headers())
    ACTOR_ID = 'apify/beautifulsoup-scraper'
    actor_client = client.actor(ACTOR_ID)  
    
    # Prepare the Actor input
    ACTOR_INPUT = {
        "startUrls": urls,
        "maxCrawlingDepth": 0,
        "requestTimeout": 30,
        "soupFeatures": "html.parser",
        "pageFunction": (
            "from typing import Any\n"
            "import re\n"
            "\n"
            "def page_function(context: Context) -> Any:\n"
            "    url = context.request['url']\n"
            "    soup = context.soup\n"
            "    \n"
            "    # Initialize data structure\n"
            "    data = {\n"
            "        'url': url,\n"
            "        'title': soup.title.string.strip() if soup.title else None,\n"
            "        'content': {},\n"
            "    }\n"
            "    \n"
            "    # Extract main content\n"
            "    # Find main content area with multiple fallback options\n"
            "    main_content = None\n"
            "    for selector in ['main', 'article', '#content', '.content', 'body']:\n"
            "        main_content = soup.find(selector)\n"
            "        if main_content:\n"
            "            break\n"
            "    \n"
            "    if main_content:\n"
           "        # Extract structured content\n"
            "        data['content']['headers'] = [\n"
            "            {'level': h.name, 'text': h.text.strip()}\n"
            "            for h in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])\n"
            "            if h.text.strip()\n"
            "        ]\n"
            "        \n"
            "        data['content']['paragraphs'] = [\n"
            "            p.text.strip()\n"
            "            for p in main_content.find_all('p')\n"
            "            if p.text.strip() and len(p.text.strip()) > 20  # Filter out short snippets\n"
            "        ]\n"
            "        \n"
            "        # Extract lists with context\n"
            "        data['content']['lists'] = []\n"
            "        for lst in main_content.find_all(['ul', 'ol']):\n"
            "            list_items = [li.text.strip() for li in lst.find_all('li') if li.text.strip()]\n"
            "            if list_items:\n"
            "                # Try to find a header or label for this list\n"
            "                list_context = None\n"
            "                prev_elem = lst.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'label'])\n"
            "                if prev_elem:\n"
            "                    list_context = prev_elem.text.strip()\n"
            "                \n"
            "                data['content']['lists'].append({\n"
            "                    'type': lst.name,  # 'ul' or 'ol'\n"
            "                    'context': list_context,\n"
            "                    'items': list_items\n"
            "                })\n"
            "        \n"
            "        # Extract any tables\n"
            "        data['content']['tables'] = []\n"
            "        for table in main_content.find_all('table'):\n"
            "            table_data = []\n"
            "            rows = table.find_all('tr')\n"
            "            for row in rows:\n"
            "                cols = row.find_all(['td', 'th'])\n"
            "                table_data.append([col.text.strip() for col in cols])\n"
            "            if table_data:\n"
            "                data['content']['tables'].append(table_data)\n"
            "    \n"
            "    return data\n"
        ),
        "proxyConfiguration": {"useApifyProxy": True, "groups": ["Datacenter"]},
        "launchContext": {
            "launchOptions": {
                "headless": True,
                "args": [
                    "--disable-web-security",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--window-size=1920x1080"
                ]
            }
        }
    }

    # Run the Actor and wait for it to finish
    run = actor_client.call(run_input=ACTOR_INPUT)

    # Fetch and return results
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        if item.get('title') is not None and item.get('title') != '403 Forbidden':
            results.append(item)       

    return results

def search_internet(query:str, max_results: Annotated[int, "Number of web to scrape"] = 3) -> Annotated[str, "Scraped content"]:
    """
    Search Skill
    Search Tool
    Search Internet Tool
    Search Internet Skill
    duckduckgo_search tool
    Performs a search on DuckDuckGo using the duckduckgo_search package.

    :param query: str, the search query.
    :param max_results: int, maximum number of results to return.
    :return: list, search results.
    """
    with DDGS(headers=get_headers()) as ddgs:
        urls = [{"url": r['href']} for r in ddgs.text(query, max_results=max_results)]
        #print(f"============ SCRAPING URLS: {urls} =============== \n")
        res = scrape_page(urls=urls)
        return str(res)

def get_current_date_time() -> Annotated[str, "Current date and time"]:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_arxiv_papers(
    title: Annotated[str, "Search keyword for the relevant papers or articles"], 
    papers_count: Annotated[int, "Number of papers to fetch"]
) -> Annotated[list, "List of papers"]:
    """
    Search Papers Tool
    Arxiv Tool
    Performs a search for papers and articles on Arxiv using the arxiv package.

    :param title: str, search keyword for the relevant papers or articles.
    :param papers_count: int, number of papers to fetch.
    :return: list, search results.
    """
    
    search_query = f'all:"{title}"'
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
                'authors': [author.name for author in result.authors],
                'summary': result.summary,
                'published': result.published,
                'journal_ref': result.journal_ref,
                'doi': result.doi,
                'primary_category': result.primary_category,
                'categories': result.categories,
                'pdf_url': result.pdf_url,
                'arxiv_url': result.entry_id
            }
        papers.append(paper_info)

    return papers