import tweepy
import time
from bs4 import BeautifulSoup
import requests
import os

# Run 'source ./keys/secrets.sh' in terminal before running the script to load
# the necessary keys
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

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

def score(flights):
    """
    Counts flights delayed, cancelled, and on time, encodes it into a scoring metric. Returns an integer with scoring metric.
    """
    delayed = 0
    cancelled = 0
    ontime = 0

    delayed_by_airline = {}
    cancelled_by_airline = {}
    ontime_by_airline = {}

    total_flights = 0

    for flight in flights:
        status_col = 6
        airline_col = 1

        if len(flight) < 7: # skip rows with less columns than expected
            continue
        if flight[status_col].strip().lower() == "departed": # skips rows for already departed flights
            continue

        total_flights += 1
        if flight[status_col].strip().lower() == "cancelled":
            cancelled += 1
            cancelled_by_airline[f"{flight[airline_col]}"] = cancelled_by_airline.get(f"{flight[airline_col]}", 0) + 1
            # This will get the current count for the airline from the dictionary, or default to 0 if it doesn't exist, then adds to it by 1.
        elif flight[status_col].strip().lower() == "on time":
            ontime += 1
            ontime_by_airline[f"{flight[airline_col]}"] = ontime_by_airline.get(f"{flight[airline_col]}", 0) + 1
        elif "Now" in flight[status_col]:
            delayed += 1
            delayed_by_airline[f"{flight[airline_col]}"] = delayed_by_airline.get(f"{flight[airline_col]}", 0) + 1
        else:
            None 
    
    score_metric = (delayed+cancelled)/total_flights # Takes the percentage of flights NOT on schedule (betwen 0 and 1, 0 being good, 1 being bad)
    most_delayed = max(delayed_by_airline, key=delayed_by_airline.get, default=None)
    most_cancelled = max(cancelled_by_airline, key=cancelled_by_airline.get, default=None)
    return score_metric, most_delayed, most_cancelled, delayed, cancelled, ontime, total_flights

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
    return

def post_status():
    """
    Pulls the score and posts the scoring metric on X.
    """
    score_metric, most_delayed, most_cancelled, delayed, cancelled, ontime, total_flights = score(pull_data())

    if score_metric > 0.5:
        badtext = f"💔 MCO is having a BAD hour. Out of {total_flights} upcoming flights:\n\t\n\t{delayed} are delayed\n\t{cancelled} are cancelled\n\t{ontime} are on time\n\t\n\tScore: {1-score_metric::.2f}"
        tweet(badtext)
        #print(badtext)
    elif score_metric < 0.5:
        goodtext = f" ❤️ MCO is having a GOOD hour. Out of {total_flights} flights:\n\t\n\t{delayed} upcoming flights delayed\n\t{cancelled} upcoming flights cancelled\n\t{ontime} upcoming flights on time\n\t\n\tScore: {1-score_metric:.2f}"
        tweet(goodtext)
        #print(goodtext)

if __name__ == "__main__":
    post_status()
    time.sleep(3600)  # Wait for 1 hour (3600 seconds)
    #print(pull_data()[0]) # remove this later: just to see if it works