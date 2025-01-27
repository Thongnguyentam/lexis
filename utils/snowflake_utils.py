
import snowflake.connector
from tqdm.auto import tqdm
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.ingestion import IngestionPipeline
from PyPDF2 import PdfReader
from llama_index.core import Document

def setup_snowflake_docs_table(connection_params):
   """
   Creates DOCS_CHUNKS_TABLE and enables change tracking.
   
   Args:
       connection_params (dict): Snowflake connection parameters
   """
   conn = snowflake.connector.connect(**connection_params)
   cursor = conn.cursor()
   
   create_table = """
   CREATE TABLE IF NOT EXISTS DOCS_CHUNKS_TABLE(
       RELATIVE_PATH VARCHAR(16777216),
       SIZE NUMBER(38,0), 
       PAGE_NUMBER NUMBER(38,0),
       FILE_URL VARCHAR(16777216),
       CHUNK VARCHAR(16777216),
       CATEGORY VARCHAR(16777216),
       CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
   )
   """
   
   try:
       cursor.execute(create_table)
       cursor.execute("ALTER TABLE DOCS_CHUNKS_TABLE SET CHANGE_TRACKING = TRUE;")
   finally:
       cursor.close()
       conn.close()
       
def insert_document_chunks(connection_params, chunks):
    """
    Inserts document chunks into DOCS_CHUNKS_TABLE.
    
    Args:
        connection_params (dict): Snowflake connection parameters
        results (list): Document chunks to insert
    """
    conn = snowflake.connector.connect(**connection_params)
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO DOCS_CHUNKS_TABLE (
        RELATIVE_PATH, 
        SIZE, 
        PAGE_NUMBER,
        CHUNK, 
        CATEGORY
    ) VALUES (%s, %s, %s, %s, %s)
    """
    
    try:
        for chunk in tqdm(chunks, desc="Inserting document chunks into Snowflake"):
            cursor.execute(insert_query, (
                chunk.metadata['file_name'],
                len(chunk.text),
                chunk.metadata['page_label'], 
                chunk.text,
                None
            ))
        conn.commit()
    except Exception as e:
        # Rollback changes if any error occurs
        conn.rollback()
        raise RuntimeError(f"Failed to insert document chunks: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def create_cortex_search_service_if_not_exists(
    connection_params, 
    service_name: str = "CC_SEARCH_SERVICE_CS", 
    table_name: str = "docs_chunks_table", 
    warehouse: str = "COMPUTE_WH", 
    target_lag='1 minute'
):
    """
    Creates a Cortex Search Service if it does not already exist.
    
    Args:
        connection_params (dict): Snowflake connection parameters.
        service_name (str): Name of the Cortex Search Service.
        table_name (str): Name of the table to index.
        warehouse (str): Name of the warehouse to use.
        target_lag (str): Target lag for refresh. Default is '1 day'.
    """
    conn = snowflake.connector.connect(**connection_params)
    cursor = conn.cursor()
    
    # Check if the Cortex Search Service exists
    check_service_query = f"""
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.CORTEX_SEARCH_SERVICES 
    WHERE SERVICE_NAME = '{service_name.upper()}'
    """
    
    create_service_query = f"""
    CREATE OR REPLACE CORTEX SEARCH SERVICE {service_name}
    ON chunk
    ATTRIBUTES category 
    WAREHOUSE = {warehouse}
    TARGET_LAG = '{target_lag}'
    AS (
        SELECT 
            chunk,
            relative_path,
            category
        FROM {table_name}
    )
    """
    
    try:
        cursor.execute(check_service_query)
        service_exists = cursor.fetchone()[0] > 0
        
        if not service_exists:
            cursor.execute(create_service_query)
            print(f"Cortex Search Service '{service_name}' created successfully.")
        else:
            print(f"Cortex Search Service '{service_name}' already exists.")
    finally:
        cursor.close()
        conn.close()
        
def process_documents(documents: list[Document]):
    """
    Processes a list of documents using Semantic Splitting

    Args:
        documents (list[Document]): List of Document objects to process.

    Returns:
        results: Processed results from the Semantic Splitting
    """
    # Initialize the embedding model
    embed_model = HuggingFaceEmbedding("Snowflake/snowflake-arctic-embed-m")
    
    # Set up the splitter node parser
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=85,
        embed_model=embed_model
    )
    
    # Create the ingestion pipeline with transformations
    cortex_search_pipeline = IngestionPipeline(
        transformations=[
            splitter,
        ],
    )
    
    # Run the pipeline on the documents
    for document in documents:
        for chunk in cortex_search_pipeline.run(show_progress=True, documents=[document]):
            yield chunk


def load_pdf_to_llamaindex(uploaded_file):
    """
    Loads a PDF file from an uploaded Streamlit file into LlamaIndex-compatible documents.

    Args:
        uploaded_file (BytesIO): The uploaded file object from Streamlit.

    Returns:
        list[Document]: A list of Document objects containing the PDF text and metadata.
    """
    # Read the PDF from the uploaded file
    reader = PdfReader(uploaded_file)
    filename = uploaded_file.name  # Extract the file name from the uploaded file object
    documents = []

    # Extract text from each page and create LlamaIndex Document objects
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        document = Document(text=text, metadata={'file_name': filename, 'page_label': page_num})        
        documents.append(document)
    
    return documents

def upload_pdf_to_snowflake(connection_params, uploaded_file):
    """
    Uploads a PDF file to Snowflake DOCS_CHUNKS_TABLE.

    Args:
        connection_params (dict): Snowflake connection parameters.
        uploaded_file (BytesIO): The uploaded file object from Streamlit.
    """

    documents = load_pdf_to_llamaindex(uploaded_file)
    chunks_generator = process_documents(documents)
    insert_document_chunks(connection_params, chunks_generator)
    
    print(f"Uploaded PDF file '{uploaded_file.name}' to Snowflake successfully.")