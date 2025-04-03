import sqlite3
import pandas as pd
from datetime import timedelta


DB_PATH = 'storage/database.db'
TABLE_NAME = 'history'

def get_score_history():
    """
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT timestamp, score_metric, cancelled, delayed, ontime
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
    cancelled = df['cancelled'].tolist()
    delayed = df['delayed'].tolist()
    ontime = df['ontime'].tolist()

    # Use the last timestamp in the dataset as the end of the range
    last_timestamp = df["timestamp"].iloc[-1]
    # Calculate the start time (24 hours before the last timestamp)
    start_time = (last_timestamp - timedelta(hours=24)).isoformat()
    end_time = last_timestamp.isoformat()

    payload = {
        'data': [
            {
                'type': 'bar',
                'name': 'Cancelled',
                'x': x,
                'y': cancelled,
                'yaxis': 'y2',
                'width': 800000,
                'marker': {'color': 'red', 'opacity': 0.7},
            },
            {
                'type': 'bar',
                'name': 'Delayed',
                'x': x,
                'y': delayed,
                'yaxis': 'y2',
                'width': 800000,
                'marker': {'color': 'orange', 'opacity': 0.7},
            },
            {
                'type': 'bar',
                'name': 'Ontime',
                'x': x,
                'y': ontime,
                'yaxis': 'y2',
                'width': 800000,
                'marker': {'color': 'green', 'opacity': 0.7},
            },
            {
                'type': 'scatter',
                'name': 'Score',
                'x': x,
                'y': y,
                'mode': 'lines',
                'yaxis': 'y1',
                'marker': {'color': 'white'},
                'layer': 'above',  # should bring the line trace in front
            },
        ],
        'layout': {
            'margin': {'l': 40, 'r': 40, 't': 15, 'b': 30},
            'autosize': True,
            #'plot_bgcolor': '#fffff',
            'paper_bgcolor':'rgba(0,0,0,0)',
            'plot_bgcolor':'rgba(0,0,0,0)',
            'yaxis': {  # Primary y-axis for score
                'title': 'Score Metrc',
                'titlefont': {'color': 'white'},
                'range': [0, 1],
                'fixedrange': True,
                'gridcolor': 'rgba(255,255,255,0.3)',
                'tickfont': {'color': 'white'},
                'linecolor': 'white',
            },
            'yaxis2': {  # Secondary y-axis for flight counts
                'title': 'Flight Counts',
                'titlefont': {'color': 'white'},
                'overlaying': 'y',
                'side': 'right',
                'fixedrange': True,
                'gridcolor': 'rgba(255,255,255,0.3)',
                'tickfont': {'color': 'white'},
                'linecolor': 'white',
            },
            'xaxis': {
                'range': [start_time, end_time],
                'titlefont': {'color': 'white'},
                'title': 'Time',
                'automargin': True,
                'linecolor': 'white',
                'tickfont': {'color': 'white'},
                
            },
            'barmode': 'stack',  # Stack bars on top of each other
            'bargap': 0.05,
            'legend': {
                'font': {'color': 'white'},
                'orientation': 'h',      # Set legend to horizontal orientation
                'x': 0.5,                # Center the legend on the x-axis
                'xanchor': 'center',     # Anchor the legend at the center
                'y': -0.2,               # Place the legend below the plot (adjust as needed)
                'yanchor': 'top'         # Anchor the top of the legend to the y position
            },
        },
    }
    return payload