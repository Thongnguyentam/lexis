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

def upload_to_stage(file, stage_name: str = "@docs"):
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
