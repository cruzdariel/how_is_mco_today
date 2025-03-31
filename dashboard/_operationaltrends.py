import sqlite3
import pandas as pd

DB_PATH = 'storage/database.db'
TABLE_NAME = 'history'

def get_score_history():
    """
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT timestamp, score_metric
        FROM history
        ORDER BY timestamp ASC 
        """, 
    conn)
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')

    return df