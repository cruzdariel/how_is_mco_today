import time
from bs4 import BeautifulSoup
import requests
import os
import math
import csv
from datetime import datetime
import subprocess
from app import pull_data, score, push_to_github, pull_tsa
from atproto import Client

BSKY_USERNAME = os.getenv("BSKY_USERNAME")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")
TSA_API_KEY = os.getenv("TSA_API_KEY")

client = Client()
client.login(BSKY_USERNAME, BSKY_PASSWORD)

score_metric, most_delayed, most_cancelled, delayed_by_airline, cancelled_by_airline, delayed, cancelled, ontime, total_flights, average_general_wait, average_precheck_wait, average_overall_wait = score(pull_data())

def bsky_post(post_text):
    """
    Posts the given text to Bluesky using the AT Protocol SDK.
    """
    try:
        client.send_post(text=post_text)
        print(f"Posted to Bluesky: {post_text}")
    except Exception as e:
        print(f"Error: {e}")
        raise

def post_bsky_status(debug):
    """
    Pulls the score and posts the scoring metric on X.
    """

    if total_flights == 0: # found out that the the script breaks if theres 0 flights, so added this redundancy
        print("No flights found. Skipping tweet.")
        return

    if score_metric == 0:
        neutral = f"💤 MCO is SLEEPING! The airport doesn't have any upcoming flights right now."
        if not debug:
            bsky_post(neutral)
        else:
            print(f"Debug Mode: {neutral}")
    elif score_metric <= 0.6:
        badtext = f"💔 MCO is having a BAD day. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\t🛂 TSA General Avg: {average_general_wait} mins\n\t⏩ TSA PreCheck Avg: {average_precheck_wait} mins\n\t\n\t‼️ Most Cancellations: {most_cancelled}\n\t❗️ Most Delays: {most_delayed}\n\t\n\tScore: {score_metric:.2f}"
        if not debug:
            bsky_post(badtext)
        else: 
            print(f"Debug Mode: {badtext}")
            print(score_metric)
    elif 0.6 < score_metric <= 0.8:
        oktext = f"❤️‍🩹 MCO is having an OK day. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\t🛂 TSA General Avg: {average_general_wait} mins\n\t⏩ TSA PreCheck Avg: {average_precheck_wait} mins\n\t\n\t‼️ Most Cancellations: {most_cancelled}\n\t❗️ Most Delays: {most_delayed}\n\t\n\tScore: {score_metric:.2f}"
        if not debug:
            bsky_post(oktext)
        else:
            print(f"Debug Mode: {oktext}")
            print(score_metric)
    elif score_metric > 0.8:
        goodtext = f"❤️ MCO is having a GOOD day. Out of {total_flights} upcoming flights:\n\t\n\t⚠️ {delayed} are delayed\n\t⛔️ {cancelled} are cancelled\n\t✅ {ontime} are on time\n\t\n\t🛂 TSA General Avg: {average_general_wait} mins\n\t⏩ TSA PreCheck Avg: {average_precheck_wait} mins\n\t\n\t‼️ Most Cancellations: {most_cancelled}\n\t❗️ Most Delays: {most_delayed}\n\t\n\tScore: {score_metric:.2f}"
        if not debug:
            bsky_post(goodtext)
        else:
            print(f"Debug Mode: {goodtext}")
            print(score_metric)

if __name__ == "__main__":
    while True:
        try:
            # recalculate data on every loop iteration
            flights = pull_data()
            tsa_data = pull_tsa()
            if not tsa_data or not flights:
                print("Data not available. Retrying after delay.")
                time.sleep(5400)
                continue

            (score_metric, most_delayed, most_cancelled, delayed_by_airline, cancelled_by_airline,
             delayed, cancelled, ontime, total_flights, average_general_wait, average_precheck_wait,
             average_overall_wait) = score(flights)

            post_bsky_status(debug=False)
            print(f"Most delayed: {most_delayed}")
            print(f"Most cancelled: {most_cancelled}")

            # write data to CSV
            csv_row = {
                'timestamp': datetime.now().isoformat(),
                'score_metric': score_metric,
                'most_delayed': most_delayed,
                'most_cancelled': most_cancelled, 
                'delayed_by_airline': str(delayed_by_airline),
                'cancelled_by_airline': str(cancelled_by_airline),
                'delayed': delayed,
                'cancelled': cancelled,
                'ontime': ontime,
                'total_flights': total_flights,
                'average_general_wait': average_general_wait,
                'average_precheck_wait': average_precheck_wait,
                'average_overall_wait': average_overall_wait,
                'open_checkpoints': tsa_data['open_checkpoints_count'],
                'lane_wait_times': str(tsa_data['lane_wait_times']),
                'source':'BSKY'
            }
            file_exists = os.path.isfile('history.csv')
            with open('history.csv', 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(csv_row)
            push_to_github()
            
            time.sleep(1800)  # wait for 0.5 hours before next post
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(1800)