#####################################################################
#####################################################################
#####███╗░░██╗░█████╗░░██████╗░██████╗████████╗░█████╗░████████╗#####
#####████╗░██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝#####
#####██╔██╗██║███████║╚█████╗░╚█████╗░░░░██║░░░███████║░░░██║░░░#####
#####██║╚████║██╔══██║░╚═══██╗░╚═══██╗░░░██║░░░██╔══██║░░░██║░░░#####
#####██║░╚███║██║░░██║██████╔╝██████╔╝░░░██║░░░██║░░██║░░░██║░░░#####
#####╚═╝░░╚══╝╚═╝░░╚═╝╚═════╝░╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░#####
##### A WRAPPER OF FAA AIRSPACE DATA BY DARIEL CRUZ RODRIGUEZ #######
#####################################################################
#####################################################################

import requests
import json
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone

class Airport():
    """
    Class that represents an airport, and provides methods to retrieve data from it.
    """
    def __init__(self, airportid):
        """
        Constructor for the Airport class, takes only one input, the FAA airport ID.

        Inputs:
            - FAA Airport ID (string): The FAA airport ID.

        Outputs:
            - None

        Example:
            > airport = Airport("MCO")
            Retrieves information from Orlando International Airport in Orlando, Florida, which uses
            the FAA airport ID "MCO". Only valid for U.S. domestic airports.
        """
        self.airportid = airportid
        self.lastupdate = None
        self.airportclosures = None
        self.airportdelays = None
        self.possibledelays = None

    def getDelays(self):
            """
            Fetches live airport delay data from the FAA NAS Status API and updates self.airportdelays.

            Outputs:
                - None (updates self.airportdelays)
            """
            
            try:
                response = requests.get("https://nasstatus.faa.gov/api/airport-status-information")
                response.raise_for_status()
            except requests.RequestException as e:
                print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error fetching data: {e}")
                return

            # Helper function: Convert text like "1 hour and 24 minutes" to minute format
            def parse_minutes(time_str):
                numbers = re.findall(r"(\d+)", time_str.lower())
                if "hour" in time_str.lower():
                    hours = int(numbers[0]) if len(numbers) >= 1 else 0
                    minutes = int(numbers[1]) if len(numbers) >= 2 else 0
                    return hours * 60 + minutes
                elif "minute" in time_str.lower():
                    return int(numbers[0]) if numbers else 0
                return 0

            # Helper function: search FAA's XML for airport delays
            def parse_faa_xml(xml_string):
                root = ET.fromstring(xml_string)
                delays = {}

                for delay_type in root.findall("Delay_type"):

                    # Ground Delays
                    for ground_delay in delay_type.findall(".//Ground_Delay"):
                        arpt = ground_delay.find("ARPT").text if ground_delay.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            reason = ground_delay.find("Reason").text if ground_delay.find("Reason") is not None else "Unknown"
                            max_delay = ground_delay.find("Max").text if ground_delay.find("Max") is not None else "0 minutes"
                            avg_delay = ground_delay.find("Avg").text if ground_delay.find("Avg") is not None else "0 minutes"
                            min_delay = avg_delay  # Approximate min delay as avg for missing data
                            
                            delays["Ground"] = {
                                "minDelay": parse_minutes(min_delay),
                                "maxDelay": parse_minutes(max_delay),
                                "avgDelay": parse_minutes(avg_delay),
                                "reason": reason
                            }

                    # Arrival/Departure Delays
                    for delay in delay_type.findall(".//Delay"):
                        arpt = delay.find("ARPT").text if delay.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            reason = delay.find("Reason").text if delay.find("Reason") is not None else "Unknown"

                            for arr_dep in delay.findall("Arrival_Departure"):
                                delay_category = arr_dep.get("Type", "Unknown")
                                min_delay = arr_dep.find("Min").text if arr_dep.find("Min") is not None else "0 minutes"
                                max_delay = arr_dep.find("Max").text if arr_dep.find("Max") is not None else "0 minutes"
                                avg_delay = (parse_minutes(min_delay) + parse_minutes(max_delay)) // 2  # Approximate avg
                                
                                delays[delay_category] = {
                                    "minDelay": parse_minutes(min_delay),
                                    "maxDelay": parse_minutes(max_delay),
                                    "avgDelay": avg_delay,
                                    "reason": reason
                                }

                return delays if delays else None

            self.airportdelays = parse_faa_xml(response.text)
            self.lastupdate = datetime.utcnow().isoformat()
            return self.airportdelays

    def getDepartureDelays(self):
        """
        Fetches departure delay data only.

        Outputs:
            - departure_delays (dict): A dictionary of departure delays with details, or None if no delays are found.
        """
        if self.airportdelays is None:
            try:
                print("\x1b[34;1mNAASTATUS\x1b[0m Airport Delays is empty, attempting to refresh...")
                self.getDelays()
            except Exception as e:
                print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error while fetching airport events: {e}")
                return None

        departure_delays = {}
        if self.airportdelays is not None:
            for category, data in self.airportdelays.items():
                if "Departure" in category:
                    departure_delays[category] = data

        return departure_delays if departure_delays else None
    
    def getArrivalDelays(self):
        """
        Fetches arrival delay data only.

        Outputs:
            - arrival_delays (dict): A dictionary of arrival delays with details, or None if no delays are found.
        """
        if self.airportdelays is None:
            try:
                print("\x1b[34;1mNAASTATUS\x1b[0m Airport Delays is empty, attempting to refresh...")
                self.getDelays()
            except Exception as e:
                print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error while fetching airport events: {e}")
                return None

        arrival_delays = {}
        if self.airportdelays is not None:
            for category, data in self.airportdelays.items():
                if "Arrival" in category:
                    arrival_delays[category] = data

        return arrival_delays if arrival_delays else None

    def getGroundDelays(self):
            """
            Fetches ground delay data only.

            Outputs:
                - ground_delays (dict): A dictionary of ground delay details, or None if no ground delays are found.
            """
            if self.airportdelays is None:
                try:
                    print("\x1b[34;1mNAASTATUS\x1b[0m Airport Delays is empty, attempting to refresh...")
                    self.getDelays()
                except Exception as e:
                    print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error while fetching airport events: {e}")
                    return None

            ground_delays = {}
            if self.airportdelays is not None:
                for category, data in self.airportdelays.items():
                    if category == "Ground":
                        ground_delays[category] = data
            else:
                return None

            return ground_delays if ground_delays else None

    def getClosures(self):
        """
        Fetches airport closure data from the FAA NAS Status API and updates self.airportclosures.
        
        Returns:
            dict: A dictionary of airport closures with details, or None if no closures are found.
        """
        try:
            response = requests.get("https://nasstatus.faa.gov/api/airport-status-information")
            response.raise_for_status()
        except requests.RequestException as e:
            print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error fetching data: {e}")
            return None

        def parse_closures(xml_string):
            root = ET.fromstring(xml_string)
            closures = []

            for delay_type in root.findall("Delay_type"):
                if delay_type.find("Name") is not None and delay_type.find("Name").text == "Airport Closures":
                    for airport in delay_type.findall(".//Airport"):
                        arpt = airport.find("ARPT").text if airport.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            closure = {
                                "reason": airport.find("Reason").text if airport.find("Reason") is not None else "Unknown",
                                "start": airport.find("Start").text if airport.find("Start") is not None else "Unknown",
                                "reopen": airport.find("Reopen").text if airport.find("Reopen") is not None else "Unknown"
                            }
                            closures.append(closure)

            return closures if closures else None

        self.airportclosures = parse_closures(response.text)
        self.lastupdate = datetime.utcnow().isoformat()
        return self.airportclosures

    def averageDelay(self):
        """
        Calculates the average delay across all delay categories.

        Returns:
            float: The average delay in minutes across all categories, or 0 if no delays exist.
        """
        if self.airportdelays is None:
            try:
                print("\x1b[34;1mNAASTATUS\x1b[0m Airport Delays is empty, attempting to refresh...")
                self.getDelays()
            except Exception as e:
                print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error while fetching airport delays: {e}")
                return 0

        if not self.airportdelays:
            return 0

        total_delay = 0
        count = 0

        for category, data in self.airportdelays.items():
            if "avgDelay" in data:
                total_delay += data["avgDelay"]
                count += 1

        return total_delay / count if count > 0 else 0

    def lastUpdated(self):
        """
        Returns the timestamp of the last update.

        Returns:
            str: The timestamp of the last update, or None if no update has occurred.
        """
        return self.lastupdate

    def delayReasons(self):
        """
        Returns a formatted string with all delay reasons.

        Returns:
            str: Comma-separated list of delay reasons, with 'and' before the last reason, 
                 or 'No delays reported' if no delays exist.
        """
        if self.airportdelays is None:
            try:
                print("\x1b[34;1mNAASTATUS\x1b[0m Airport Delays is empty, attempting to refresh...")
                self.getDelays()
            except Exception as e:
                print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error while fetching airport delays: {e}")
                return None

        if not self.airportdelays:
            return None

        reasons = []
        for category, data in self.airportdelays.items():
            if "reason" in data and data["reason"] not in reasons:
                reasons.append(data["reason"])

        if not reasons:
            return "No specific reasons reported"
        elif len(reasons) == 1:
            return reasons[0]
        elif len(reasons) == 2:
            return f"{reasons[0]} and {reasons[1]}"
        else:
            return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"
    
    def isDelay(self):
        """
        Returns True if the airport is experiencing delays, False otherwise.

        Inputs:
            - None
        Outputs:
            - Boolean: True if the airport is experiencing delays, False otherwise.
        """
        if self.airportdelays is None:
            try:
                print("\x1b[34;1mNAASTATUS\x1b[0m Airport Delays is empty, attempting to refresh...")
                self.getDelays()
            except Exception as e:
                print("\x1b[34;1mNAASTATUS\x1b[0m " + f"Error while fetching airport events: {e}")
                return False 

        return self.airportdelays is not None
    
    def getPossibleDelays(self):
        """
        Fetches possible future delays from the FAA operations plan API.
        Only retrieves events that specifically mention the airport code.

        Updates:
            self.possibledelays: Dictionary of possible delays or None if no data available
        """
        try:
            response = requests.get("https://nasstatus.faa.gov/api/operations-plan")
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"\x1b[34;1mNAASTATUS\x1b[0m Error fetching operations plan: {e}")
            self.possibledelays = None
            return

        possible_delays = {}
        
        # Check terminal planned events
        if "terminalPlanned" in data:
            for event in data["terminalPlanned"]:
                event_text = event.get("event", "")
                if self.airportid in event_text:
                    delay_type = re.sub(r'/([A-Z]{3})\b', '', event_text)
                    delay_type = re.sub(r'^([A-Z]{3})\b/?', '', delay_type).strip()
                    possible_delays[delay_type] = event.get("time", "")
        
        # Check enroute planned events
        if "enRoutePlanned" in data:
            for event in data["enRoutePlanned"]:
                event_text = event.get("event", "")
                if self.airportid in event_text:
                    delay_type = re.sub(r'/[A-Z]{3}', '', event_text)
                    delay_type = re.sub(r'^[A-Z]{3}/?', '', delay_type).strip()
                    possible_delays[delay_type] = event.get("time", "")
        
        self.possibledelays = possible_delays if possible_delays else None
        self.lastupdate = datetime.utcnow().isoformat()
        return self.possibledelays
