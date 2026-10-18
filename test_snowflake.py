import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

try:
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator="externalbrowser",
        warehouse="COMPUTE_WH",
        database="SNOWFLAKE_SAMPLE_DATA",
        schema="TPCH_SF1",
        login_timeout=60,
    )

    cur = conn.cursor()
    cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE()")
    print("SUCCESS:", cur.fetchone())
    cur.close()
    conn.close()

except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR:", e)