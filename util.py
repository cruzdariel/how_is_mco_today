import requests
import json

# ORLANDO AIRPORT SPECIFIC FUNCTIONS
def get_flight_board():
    """
    Returns a pandas DataFrame containing upcoming departures and arrivals.
    """
    APIKEY_GOAA = os.getenv("APIKEY_GOAA")
    URL = "https://api.goaa.aero/flights/get?scheduledTimestamp=1740986543..1741116143"
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
    """
    APIKEY_GOAA = os.getenv("APIKEY_GOAA")
    URL = "https://api.goaa.aero/parking/availability/MCO"
    HEADER = {"api_key":APIKEY_GOAA}

    if not APIKEY:
        raise ValueError("APIKEY environment variable is not set.")

# FAA FUNCTIONS / NATIONAL AIRSPACE

# SCORING
def score():
    return

# POSTING ON SOCIALS

# SQL DATABASE 

def write(input):
    return

def read(input):
    return