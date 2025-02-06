import tweepy
import time
from bs4 import BeautifulSoup
import requests
import os

# Make sure to run 'source ./keys/secrets.sh', or wherever your secrets file is 
# in terminal before running the script to load the necessary keys securely
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

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
    
    score_metric = (delayed+cancelled)/total_flights # takes the percentage of flights NOT on schedule (betwen 0 and 1, 0 being good, 1 being bad)
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
        raise
    return

def post_status():
    """
    Pulls the score and posts the scoring metric on X.
    """
    score_metric, most_delayed, most_cancelled, delayed, cancelled, ontime, total_flights = score(pull_data())

    if total_flights == 0: # found out that the the script breaks if theres 0 flights, so added this redundancy
        print("No flights found. Skipping tweet.")
        return

    if score_metric > 0.5:
        badtext = f"💔 MCO is having a BAD hour. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\tScore: {1-score_metric:.2f}"
        tweet(badtext)
    elif score_metric < 0.5:
        goodtext = f"❤️ MCO is having a GOOD hour. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\tScore: {1-score_metric:.2f}"
        tweet(goodtext)

if __name__ == "__main__":
    while True:
        try:
            post_status()
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