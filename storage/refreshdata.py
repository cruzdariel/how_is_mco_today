import sqlite3

def stage_data():
    #value1 = ...
    # eventually ill handle the data here
    return value1, value2, value3
def write_to_db(value1, value2, value3):
    query = """
    INSERT INTO history (
        value1,
        value2,
        value3
    ) VALUES (?, ?, ?)
    """

    values = (value1, value2, value3)
    cursor.execute(query, values)
    conn.commit()
    conn.close()

