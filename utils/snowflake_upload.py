import snowflake.connector
from config import SNOWFLAKE_ACCOUNT, SNOWFLAKE_DATABASE, SNOWFLAKE_PASSWORD, SNOWFLAKE_SCHEMA, SNOWFLAKE_USER, SNOWFLAKE_WAREHOUSE
import os

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

def upload_to_stage(file, stage_name: str = "docs"):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Save file locally
        local_path = os.path.join("temp", file.name)
        with open(local_path, "wb") as f:
            f.write(file.getbuffer())

        # Snowflake PUT command
        put_command = f"PUT file://{local_path} @{stage_name};"
        cursor.execute(put_command)

        os.remove(local_path)
        conn.close()
        
        return f"File '{file.name}' successfully uploaded to stage {stage_name}."
    except Exception as e:
        print(e)
        return f"Error uploading file to stage: {str(e)}"
    
def load_data_from_stage(stage_name:str= "@docs", table_name: str = "DOCS_CHUNKS_TABLE"):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    copy_command = f"""
    COPY INTO {table_name}
    FROM {stage_name}
    FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY='"');
    """
    cursor.execute(copy_command)
    st.success(f"Data loaded successfully into table: {table_name}")