import requests
import json
import pandas as pd
import os
import sqlite3

# ORLANDO AIRPORT SPECIFIC FUNCTIONS
def get_flights(start, end):
    """
    Returns a pandas DataFrame containing upcoming departures and arrivals.
    """
    APIKEY_GOAA = os.getenv("APIKEY_GOAA")
    URL = f"https://api.goaa.aero/flights/get?scheduledTimestamp={start}..{end}"
    HEADER = {
        "api-key": APIKEY_GOAA,
        "api-version": "140",
        "Accept": "application/json"
        }

    if not APIKEY_GOAA:
        raise ValueError("APIKEY environment variable is not set.")

    response = requests.post(url=URL, headers=HEADER)

    if response.status_code != 200:
        raise ValueError("API request failed.")
    
    json_response = response.json()

    results = []
    columnnames = ["id", "airline", "num", "scheduled", 
                "actual", "diff", "origin", "destination",
                "type", "status"]
    
    if not json_response["data"]["flight_list"]:
        raise ValueError("Couldn't find flight data")

    for flight in json_response["data"]["flight_list"]:
        id = flight["id"]
        airline = flight["mainAirlineName"]
        num = flight["mainSuffix"]
        scheduled = flight["scheduledTimestamp"]
        actual = flight["lastKnownTimestamp"]
        diff = int(scheduled) - int(actual) # negative if delayed, positive if early
        origin = flight["originAirport"]
        destination = flight["destinationAirport"]
        flighttype = "arrival" if flight['arrival'] else "departure"
        status = flight["status"] # ON -> on time, AR -> arrived, DP -> departed, DL -> delayed, CX -> cancelled

        results.append([id, airline, num, scheduled, actual, diff, origin, destination, flighttype, status])
    
    flights = pd.DataFrame(results, columns=columnnames)

    return flights
    
def get_parking_loads():
    """
    Returns a pandas DataFrame containing the parking availability of each garage with
    it's Status, EV Charging, and Parking Rates.

    There are two endpoints:
        - https://api.goaa.aero/parking/rates/MCO
        - https://api.goaa.aero/parking/availability/MCO
    """
    APIKEY_GOAA = os.getenv("APIKEY_GOAA")
    URL_PARKING = "https://api.goaa.aero/parking/availability/MCO"
    URL_RATES = "https://api.goaa.aero/parking/rates/MCO"
    HEADER = {"api-key":APIKEY_GOAA,
        "api-version": "140",
        "Accept": "application/json"}

    if not APIKEY_GOAA:
        raise ValueError("APIKEY environment variable is not set.")

    # Parking availability 

    response_parking = requests.get(url=URL_PARKING, headers=HEADER)

    if response_parking.status_code != 200:
        raise ValueError(f"API request failed. {response_parking}")
    
    json_response_parking = response_parking.json()

    results_parking = []
    columnnames_parking = ["id", "garagename", "category", "status", "ev"]
    
    if not json_response_parking["data"]["parkingAvailability"]:
        raise ValueError("Couldn't find flight data")
    
    for garage in json_response_parking["data"]["parkingAvailability"]:
        id = garage["id"]
        garagename = garage["name"]
        category = garage["category"]
        status = garage["status"]
        ev = garage["attributes"]["ev"]

        results_parking.append([id, garagename, category, status, ev])
    
    # Garage Rates
    
    response_rates = requests.get(url=URL_RATES, headers=HEADER)

    if response_rates.status_code != 200:
        raise ValueError("API request failed.")
    
    json_response_rates = response_rates.json()

    results_rates = []
    columnnames_rates = ["id", "rate"]
    
    if not json_response_rates["data"]["rates"]:
        raise ValueError("Couldn't find flight data")
    
    for garage in json_response_rates["data"]["rates"]:
        id = garage["id"]
        rate = garage["rate"]

        results_rates.append([id, rate])
    
    garage_df = pd.DataFrame(results_parking, columns=columnnames_parking)
    rates_df = pd.DataFrame(results_rates, columns=columnnames_rates)
    parking_df = garage_df.merge(rates_df, how="left", on="id")
    
    return parking_df

def get_security_waits():
    APIKEY_GOAA = os.getenv("APIKEY_GOAA")
    URL = f"https://api.goaa.aero/wait-times/checkpoint/MCO"
    HEADER = {
        "api-key": APIKEY_GOAA,
        "api-version": "140",
        "Accept": "application/json"
        }

    if not APIKEY_GOAA:
        raise ValueError("APIKEY environment variable is not set.")

    response = requests.get(url=URL, headers=HEADER)

    if response.status_code != 200:
        raise ValueError(f"API request failed: {response.status_code}")
    
    json_response = response.json()

    results = []
    columnnames = ["id", "name", "type", "averagewait", "isopen"]
    
    if not json_response["data"]["wait_times"]:
        raise ValueError("Couldn't find wait data")

    for chkpt in json_response["data"]["wait_times"]:
        id = chkpt["id"]
        name = chkpt["name"]
        type = chkpt["lane"]
        averagewait = int(chkpt["waitSeconds"])/60
        isopen = chkpt["isOpen"]

        results.append([id, name, type, averagewait, isopen])
    
    security_df = pd.DataFrame(results, columns=columnnames)
    return security_df

def get_data(start, end):
    """
    Fetch data from flights, parking, and security systems.
    Parameters:
        start: The starting point (date/time) to filter the flight data.
        end: The ending point (date/time) to filter the flight data.
    Returns:
        tuple: A tuple containing:
            - flights data from get_flights(start, end)
            - parking loads data from get_parking_loads()
            - security wait times from get_security_waits()
    """
    return get_flights(start, end), get_parking_loads(), get_security_waits()

# FAA FUNCTIONS / NATIONAL AIRSPACE

# SCORING
def score():
    return

# POSTING ON SOCIALS

def post(platform, debug=False):
    return

# SQL DATABASE 

def read(input):
    """
    Retrieves data from the 'history' table in the SQLite database and returns a pandas DataFrame.
    Parameters:
        input (str): The column expression(s) to select from the 'history' table.
    Returns:
        pandas.DataFrame: A DataFrame containing the query results.
    Note:
        - The results are ordered in ascending order by the 'timestamp' field.
        - The SQL query is constructed using formatted string interpolation
    """
    DB_PATH = 'storage/database.db'
    TABLE_NAME = 'history'
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"""
        SELECT {input}
        FROM history
        ORDER BY timestamp ASC 
        """, 
    conn)
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')

    return df

def write(values):
    """
    Inserts a new row into the 'history' table using the provided list of values.
    
    Parameters:
        values (list): A list of values corresponding to the columns of the history table.
        
    Note:
        The order and number of values must match the structure of the 'history' table.
    """
    conn = sqlite3.connect("storage/database.db")
    cursor = conn.cursor()
    placeholders = ', '.join('?' for _ in values)
    sql_query = f"INSERT INTO history VALUES ({placeholders})"
    
    try:
        cursor.execute(sql_query, values)
        conn.commit()
    except sqlite3.Error as e:
        print("An error occurred:", e)
        conn.rollback()
    finally:
        conn.close()