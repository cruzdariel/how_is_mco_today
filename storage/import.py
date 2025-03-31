# This imports from the csv that currently exists.abs
import pandas as pd
import sqlite3

# 1. Load the CSV from GitHub
csv_url = 'https://raw.githubusercontent.com/cruzdariel/how_is_mco_today/main/history.csv'
df = pd.read_csv(csv_url)

# 2. Ensure JSON-like columns are strings (for SQLite TEXT fields)
json_columns = ['delayed_by_airline', 'cancelled_by_airline', 'lane_wait_times']
for col in json_columns:
    df[col] = df[col].apply(lambda x: str(x) if pd.notnull(x) else '{}')

# 3. Connect to the existing SQLite database in the same directory
conn = sqlite3.connect('storage/database.db')
cursor = conn.cursor()

# 4. Insert the data into the 'history' table
df.to_sql('history', conn, if_exists='append', index=False)

# 5. Done
conn.commit()
conn.close()

print("Data imported into 'history' table in database.db")
