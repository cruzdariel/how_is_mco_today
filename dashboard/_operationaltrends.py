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

def get_params():
    df = get_score_history()
    x = [ts.isoformat() for ts in df["timestamp"]]
    y = df['score_metric'].tolist()

    payload = {
        'data': [
            {
                'type': 'scatter',
                'name': 'Trace 1',
                'x': x,
                'y': y,
            },
        ],
        'layout': {
            'margin': {'l': 15, 'r': 15, 't': 15, 'b': 15},
            'plot_bgcolor': '#fffff',
        },
    }
    return payload
