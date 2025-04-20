import mysql.connector
from mysql.connector import Error
import ast

DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database'
}

def connect():
    """Create a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def read_query(query, params=None):
    """Execute a SELECT query and return all results."""
    conn = connect()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error reading from database: {e}")
        return []
    finally:
        conn.close()

def write_query(query, params=None):
    """Execute an INSERT, DELETE, or any non-SELECT query."""
    conn = connect()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True
    except Error as e:
        print(f"Error writing to database: {e}")
        return False
    finally:
        conn.close()

def update_query(query, params=None):
    """Execute an UPDATE query."""
    return write_query(query, params)

def insert_snapshot_row(row):
    conn = connect()
    if not conn:
        print("DB connection failed.")
        return
    
    try:
        cursor = conn.cursor()

        # 1. INSERT INTO snapshots
        snapshot_sql = '''
        INSERT INTO snapshots (
            timestamp, score_metric, most_delayed, most_cancelled,
            delayed, cancelled, ontime, total_flights,
            average_general_wait, average_precheck_wait, average_overall_wait,
            open_checkpoints, source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        snapshot_values = (
            row['timestamp'], float(row['score_metric']), row['most_delayed'], row['most_cancelled'],
            int(row['delayed']), int(row['cancelled']), int(row['ontime']), int(row['total_flights']),
            float(row['average_general_wait']), float(row['average_precheck_wait']), float(row['average_overall_wait']),
            int(row['open_checkpoints']), row['source']
        )
        cursor.execute(snapshot_sql, snapshot_values)
        snapshot_id = cursor.lastrowid  # needed for foreign keys

        # 2. INSERT INTO airline_metrics
        delays = ast.literal_eval(row['delayed_by_airline']) if row['delayed_by_airline'] else {}
        cancels = ast.literal_eval(row['cancelled_by_airline']) if row['cancelled_by_airline'] else {}
        all_airlines = set(delays.keys()).union(set(cancels.keys()))

        for airline in all_airlines:
            delay_count = delays.get(airline, 0)
            cancel_count = cancels.get(airline, 0)
            cursor.execute(
                '''INSERT INTO airline_metrics (snapshot_id, airline_name, delay_count, cancel_count)
                   VALUES (%s, %s, %s, %s)''',
                (snapshot_id, airline, delay_count, cancel_count)
            )

        # 3. INSERT INTO checkpoint_waits
        checkpoints = ast.literal_eval(row['lane_wait_times'])
        for name, info in checkpoints.items():
            cursor.execute(
                '''INSERT INTO checkpoint_waits (snapshot_id, checkpoint_name, lane_type, wait_time)
                   VALUES (%s, %s, %s, %s)''',
                (snapshot_id, name, info['lane_type'], float(info['wait_time']))
            )

        conn.commit()
        print(f"Inserted snapshot {snapshot_id} successfully.")
        
    except Exception as e:
        print(f"Error inserting row: {e}")
        conn.rollback()
    finally:
        conn.close()