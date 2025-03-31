from nicegui import ui
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import sys
import os
import asyncio
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nasstat_local import Airport
import util
import _operationaltrends

# All data
#url = 'https://raw.githubusercontent.com/cruzdariel/how_is_mco_today/refs/heads/main/history.csv'
#df = pd.read_csv(url)

def get_df_from_db():
    DB_PATH = 'storage/database.db'
    TABLE_NAME = 'history'
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT *
        FROM history
        ORDER BY timestamp ASC 
        """, 
    conn)
    conn.close()
    return df

# Last 24 hours


@ui.page('/', title="Dashboard | How is MCO Today")
def main():

    df = get_df_from_db()

    # Latest data
    latest = df.iloc[-1]

    def update_data():
        """
        Refreshes data on the home page
        """
        df = get_df_from_db()
        latest = df.iloc[-1]
        plot.update()
        cancelledcount.set_text(f"{latest['cancelled']}")
        delayedcount.set_text(f"{latest['delayed']}")
        mostcancelled.set_text(f"{latest['most_cancelled']}")
        mostdelayed.set_text(f"{latest['most_delayed']}")
        lastupdated.set_text(f"Last updated: {latest['timestamp']}")

        render_tsa_cards()
        ui.notification(message="Refreshed!", timeout=3)
        
    with ui.row().classes('items-center justify-center w-full'):
        lastupdated = ui.label(f"Last updated: {latest['timestamp']}").classes('italic')
        ui.button('Update data', on_click=lambda: update_data())

    ui.separator().classes('mb-5')

    with ui.row().classes('items-center justify-center w-full'):
        with ui.column().classes('items-start'):
            ui.label('How is MCO').classes('text-5xl font-light')
            ui.label('today?').classes('text-7xl font-bold text-black-900')
            ui.link('by Dariel Cruz Rodriguez', 'https://dariel.us').classes('text-sm mt-4 inline')
            with ui.button('Sponsor This Project', on_click=lambda: ui.run_javascript('window.open("https://ko-fi.com/darielc")')).classes('bg-green'):
                    ui.tooltip('Thank you for supporting my work! <3').classes('bg-black')

        with ui.column().classes('items-end ml-20'):
            # Number of Cancellations
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Cancelled Flights').classes('text-xl')
                with ui.column().classes('items-end'):
                    cancelledcount = ui.label(f"{latest['cancelled']}").classes('text-5xl font-semibold')
                    ui.label('flights').classes('text-sm text-black-600')
                    ui.label('(comparison text)').classes('text-sm text-green-600')
            # Most Cancellations
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Most Cancellations').classes('text-xl')
                with ui.column().classes('items-end'):
                    mostcancelled = ui.label(f"{latest['most_cancelled']}").classes('text-5xl font-semibold')

        with ui.column().classes('items-end ml-20'):
            # Number of Delays
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Delayed Flights').classes('text-xl')
                with ui.column().classes('items-end'):
                    delayedcount = ui.label(f"{latest['delayed']}").classes('text-5xl font-semibold')
                    ui.label('flights').classes('text-sm text-black-600')
                    ui.label('(comparison text)').classes('text-sm text-green-600')
            # Most Delays
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Most Delays').classes('text-xl')
                with ui.column().classes('items-end'):
                    mostdelayed = ui.label(f"{latest['most_delayed']}").classes('text-5xl font-semibold')

    with ui.column().classes('w-full items-center justify-center'):
        with ui.row(wrap=True).classes('w-full'):

            with ui.column().classes('flex-[2] items-center justify-center'):

                ui.label("Operational Trends").classes('text-2xl font-semibold')

                data = _operationaltrends.get_params()
                plot = ui.plotly(data).classes('w-full h-15')

            with ui.column().classes('flex-[1] items-center justify-center'):

                ui.label("TSA Waits").classes('text-2xl font-semibold')
                waitsdf = util.get_security_waits()
                tsa_container_wrapper = ui.column().classes('w-full')  # This is where cards will go

                def render_tsa_cards():
                    tsa_container_wrapper.clear()  # THIS IS the actual container being cleared

                    waitsdf = util.get_security_waits()
                    if len(waitsdf) <= 0:
                        with tsa_container_wrapper:
                            ui.label("Error fetching TSA wait times")
                        return

                    for _, lane in waitsdf.iterrows():
                        with tsa_container_wrapper:
                            with ui.card().classes("w-full"):
                                ui.label(f"{lane['name']}").classes('text-xl font-semibold')
                                ui.label(f"Wait Time: {lane['averagewait']}")

                render_tsa_cards()


            with ui.column().classes('flex-[1.5] items-center justify-center'):

                ui.label("Active ATC Advisories").classes('text-2xl font-semibold')

                airportcode = "MCO"
                airport = Airport(airportcode)
                airport.getDelays()

                if airport.airportdelays is None:
                    image = ui.image().classes('w-1/2')

                    def get_cat():
                        try:
                            response = requests.get("https://api.thecatapi.com/v1/images/search")
                            response.raise_for_status()
                            cat_url = response.json()[0]["url"]
                            image.set_source(cat_url)
                        except Exception as e:
                            print("Error fetching cat image:", e)

                    get_cat()
                    ui.timer(60.0, get_cat)
                    ui.label("There are no delays.")
                else:
                    for key, value in airport.airportdelays.items():
                            ui.chat_message(
                                f"There is a delay on {airportcode} {key}s averaging {value['avgDelay']} minutes \
                                    (btwn. {value['minDelay']}-{value['maxDelay']} min) due to {value['reason']}.",
                                name='Air Traffic Control',
                                stamp=None,
                                avatar='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Seal_of_the_United_States_Federal_Aviation_Administration.svg/1200px-Seal_of_the_United_States_Federal_Aviation_Administration.svg.png'
                            )


ui.run()