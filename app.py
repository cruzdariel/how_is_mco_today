import tweepy
import time
from bs4 import BeautifulSoup
import requests
import os
import math
import csv
from datetime import datetime


# Make sure to run 'source ./keys/secrets.sh', or wherever your secrets file is 
# in terminal before running the script to load the necessary keys securely
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
TSA_API_KEY = os.getenv("TSA_API_KEY")

client = tweepy.Client(
                    consumer_key=API_KEY, 
                    consumer_secret=API_SECRET,
                    access_token=ACCESS_TOKEN, 
                    access_token_secret=ACCESS_SECRET
                    ) 

def pull_data():
    """
    Scrapes the old MCO airport ArrowCast departures board, returns a list of flights from the table scraped.
    Requires: BeautifulSoup, Requests
    """
    url = "https://www.arrowcast.net/fids/mco/fids.asp?sort=@schedule&sortorder=asc&city=&number=&airline=&adi=D"
    response = requests.get(url)
    flights = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        departures = soup.find("tbody")

        if departures:
            for flight in departures.find_all("tr"):
                cells = flight.find_all("td")
                try: 
                    flightinfo = [cell.get_text(strip=True) for cell in cells]
                    flights.append(flightinfo)
                except:
                    print(f"Error: is this row too long? Row length: {len(cells)}")
    return flights

def pull_tsa():
    """
    Calls the GOAA API to retrive the TSA wait times for all open checkpoints, distinguishes them between PreCheck
    and non PreCheck, and then returns a dictionary containing: average_general_wait, average_precheck_wait, average_overall_wait,
    open_checkpoints_count, and lane_wait_times (which holds another list with all wait times for each lane)
    """
    url = "https://acc.api.goaa.aero/wait-times/checkpoint/MCO"
    headers = {
        "api-key": TSA_API_KEY,
        "api-version": "140",
        "Accept": "application/json"
        }
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return None  

    if "data" not in data or "wait_times" not in data["data"]:
        print("Invalid response format.")
        return None

    open_checkpoints = [cp for cp in data["data"]["wait_times"] if cp["isOpen"]]
    
    general_wait_times = []
    precheck_wait_times = []
    lane_wait_times = {}  

    for checkpoint in open_checkpoints:
        wait_time = checkpoint["waitSeconds"] / 60  # seconds -> minutes
        lane_type = checkpoint["lane"]
        lane_name = checkpoint["name"]

        lane_wait_times[lane_name] = {"lane_type": lane_type, "wait_time": wait_time}  # Store in dictionary

        if lane_type == "tsa_precheck":
            precheck_wait_times.append(wait_time)
        elif lane_type == "general":
            general_wait_times.append(wait_time)

    avg_general = sum(general_wait_times) / len(general_wait_times) if general_wait_times else None
    avg_precheck = sum(precheck_wait_times) / len(precheck_wait_times) if precheck_wait_times else None

    all_wait_times = general_wait_times + precheck_wait_times
    avg_overall = sum(all_wait_times) / len(all_wait_times) if all_wait_times else None

    return {
        "average_general_wait": avg_general,
        "average_precheck_wait": avg_precheck,
        "average_overall_wait": avg_overall,
        "open_checkpoints_count": len(open_checkpoints),
        "lane_wait_times": lane_wait_times 
    }


def score(flights):
    """
    Counts flights delayed, cancelled, and on time, encodes it into a scoring metric. Returns an 
    integer with scoring metric.
    """
    delayed = 0
    cancelled = 0
    ontime = 0

    delayed_by_airline = {}
    cancelled_by_airline = {}
    ontime_by_airline = {}
    average_general_wait = int(pull_tsa()['average_general_wait'])
    average_precheck_wait = int(pull_tsa()['average_precheck_wait'])
    average_overall_wait = int(pull_tsa()['average_overall_wait'])

    total_flights = 0

    for flight in flights:
        status_col = 6
        airline_col = 1
        
        if len(flight) < 7: # skip rows with less columns than expected
            continue
        if flight[status_col].strip().lower() in {"departed", "closed"}: # skip already departed flights
            continue

        if flight[status_col].strip().lower() == "cancelled":
            cancelled += 1
            total_flights += 1
            cancelled_by_airline[f"{flight[airline_col]}"] = cancelled_by_airline.get(f"{flight[airline_col]}", 0) + 1
            # This will get the current count for the airline from the dictionary, or default to 0 if it doesn't exist, then adds to it by 1.
        elif flight[status_col].strip().lower() in {"on time", "last call", "boarding"}:
            ontime += 1
            total_flights += 1
            ontime_by_airline[f"{flight[airline_col]}"] = ontime_by_airline.get(f"{flight[airline_col]}", 0) + 1
        elif "now" in flight[status_col].strip().lower() or flight[status_col].strip().lower() == "delayed":
            delayed += 1
            total_flights += 1
            delayed_by_airline[f"{flight[airline_col]}"] = delayed_by_airline.get(f"{flight[airline_col]}", 0) + 1
        else:
            pass 

    # The full scoring equation can be found on Desmos: https://www.desmos.com/calculator/zxyds6lsls
    alpha = 0.40  # cancellations weight
    beta  = 0.30  # delays weight
    gamma = 0.20  # TSA general wait weight
    delta = 0.10  # TSA precheck wait weight

    if total_flights:
        ratio_cancelled = cancelled / total_flights
        ratio_delayed   = delayed / total_flights
    else:
        ratio_cancelled = 0
        ratio_delayed   = 0

    # Cancellations component:
    #   logistic function: 1 / (1 + exp(-70*(cancelled/total_flights) + 3))
    #   constant: 1 / (1 + exp(3))
    logistic_cancelled = 1 / (1 + math.exp(-70 * ratio_cancelled + 3))
    constant_cancelled = 1 / (1 + math.exp(3))
    cancellation_score = alpha * (1 - (logistic_cancelled - constant_cancelled))

    # Delays component:
    #   logistic function: 1 / (1 + exp(-15*(delayed/total_flights) + 3))
    #   constant: 1 / (1 + exp(3))
    logistic_delayed = 1 / (1 + math.exp(-15 * ratio_delayed + 3))
    constant_delayed = 1 / (1 + math.exp(3))
    delay_score = beta * (1 - (logistic_delayed - constant_delayed))

    # TSA general wait component:
    #   logistic function: 1 / (1 + exp(-0.1*(average_general_wait - 50)))
    #   constant: 1 / (1 + exp(5))
    logistic_general = 1 / (1 + math.exp(-0.1 * (average_general_wait - 50)))
    constant_general = 1 / (1 + math.exp(5))
    tsa_general_score = gamma * (1 - (logistic_general - constant_general))

    # TSA precheck wait component:
    #   logistic function: 1 / (1 + exp(-0.1*(average_precheck_wait - 15)))
    #   constant: 1 / (1 + math.exp(1.5))
    logistic_precheck = 1 / (1 + math.exp(-0.1 * (average_precheck_wait - 15)))
    constant_precheck = 1 / (1 + math.exp(1.5))
    tsa_precheck_score = delta * (1 - (logistic_precheck - constant_precheck))

    # Final score is the sum of the weighted components:
    score_metric = cancellation_score + delay_score + tsa_general_score + tsa_precheck_score
    most_delayed = max(delayed_by_airline, key=delayed_by_airline.get, default=None)
    most_cancelled = max(cancelled_by_airline, key=cancelled_by_airline.get, default=None)
    return score_metric, most_delayed, most_cancelled, delayed_by_airline, cancelled_by_airline, delayed, cancelled, ontime, total_flights, average_general_wait, average_precheck_wait, average_overall_wait

score_metric, most_delayed, most_cancelled, delayed_by_airline, cancelled_by_airline, delayed, cancelled, ontime, total_flights, average_general_wait, average_precheck_wait, average_overall_wait = score(pull_data())

def tweet(post_text):
    """
    Posts input text on X.
    Requires: Tweepy
    """
    try:
        client.create_tweet(text=post_text)
        print(f"Tweeted: {post_text}")
    except tweepy.TweepyException as e:
        print(f"Error: {e}")
        raise
    return

def post_status(debug):
    """
    Pulls the score and posts the scoring metric on X.
    """

    if total_flights == 0: # found out that the the script breaks if theres 0 flights, so added this redundancy
        print("No flights found. Skipping tweet.")
        return

    if score_metric == 0:
        neutral = f"💤 MCO is SLEEPING! The airport doesn't have any upcoming flights right now."
        if not debug:
            tweet(neutral)
        else:
            print(f"Debug Mode: {neutral}")
    elif score_metric <= 0.6:
        badtext = f"💔 MCO is having a BAD day. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\t🛂 TSA General Avg: {average_general_wait} mins\n\t⏩ TSA PreCheck Avg: {average_precheck_wait} mins\n\t\n\t‼️ Most Cancellations: {most_cancelled}\n\t❗️ Most Delays: {most_delayed}\n\t\n\tScore: {score_metric:.2f}"
        if not debug:
            tweet(badtext)
        else: 
            print(f"Debug Mode: {badtext}")
            print(score_metric)
    elif 0.6 < score_metric <= 0.8:
        oktext = f"❤️‍🩹 MCO is having an OK day. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\t🛂 TSA General Avg: {average_general_wait} mins\n\t⏩ TSA PreCheck Avg: {average_precheck_wait} mins\n\t\n\t‼️ Most Cancellations: {most_cancelled}\n\t❗️ Most Delays: {most_delayed}\n\t\n\tScore: {score_metric:.2f}"
        if not debug:
            tweet(oktext)
        else:
            print(f"Debug Mode: {oktext}")
            print(score_metric)
    elif score_metric > 0.8:
        goodtext = f"❤️ MCO is having a GOOD day. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\t🛂 TSA General Avg: {average_general_wait} mins\n\t⏩ TSA PreCheck Avg: {average_precheck_wait} mins\n\t\n\t‼️ Most Cancellations: {most_cancelled}\n\t❗️ Most Delays: {most_delayed}\n\t\n\tScore: {score_metric:.2f}"
        if not debug:
            tweet(goodtext)
        else:
            print(f"Debug Mode: {goodtext}")
            print(score_metric)

if __name__ == "__main__":
    while True:
        try:
            # Make a tweet
            post_status(debug=True)
            print(f"Most delayed: {most_delayed}")
            print(f"Most cancelled: {most_cancelled}")

            # Write data to CSV
            csv_row = {
                'timestamp': datetime.now().isoformat(),
                'score_metric': score_metric,
                'most_delayed': most_delayed,
                'most_cancelled': most_cancelled, 
                'delayed_by_airline': str(delayed_by_airline),
                'delayed': delayed,
                'cancelled': cancelled,
                'ontime': ontime,
                'total_flights': total_flights,
                'average_general_wait': average_general_wait,
                'average_precheck_wait': average_precheck_wait,
                'average_overall_wait': average_overall_wait,
                'open_checkpoints': pull_tsa()['open_checkpoints_count'],
                'lane_wait_times': str(pull_tsa()['lane_wait_times'])
            }
            file_exists = os.path.isfile('history.csv')
            with open('history.csv', 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(csv_row)
            
            time.sleep(5400)  # wait for 1.5 hours before next post
        except tweepy.errors.TooManyRequests as error1:
            # i also learned that Twitter has a limit on posting tweets. this will make the code wait
            # 24 hours or whatever time is given before trying again. (API limit is 17 tweets/24 hours for 
            # free bots). this takes all the reset times in the error header, and forces the bot to wait whatever
            # the longest reset time before running again is to avoid calling X and getting rate limited
            
            current_time = int(time.time())

            rate_reset_time = int(error1.response.headers.get("x-user-limit-24hour-reset", current_time + 900))  
            app_reset_time = int(error1.response.headers.get("x-app-limit-24hour-reset", current_time + 900))
            final_reset_time = max(rate_reset_time, app_reset_time)
            remaining_requests = int(error1.response.headers.get("x-rate-limit-remaining", 1))  # Default to 1 to be safe
            
            seconds_until_reset = max(final_reset_time - current_time, 900)  # default 15 min

            print(f"No remaining API requests. Sleeping for {seconds_until_reset} seconds.")
            time.sleep(seconds_until_reset)