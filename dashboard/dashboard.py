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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nasstat_local import Airport
import util

# All data
url = 'https://raw.githubusercontent.com/cruzdariel/how_is_mco_today/refs/heads/main/history.csv'
df = pd.read_csv(url)

# Latest data
latest = df.iloc[-1]

# Last 24 hours
now = pd.Timestamp.utcnow()
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, format='ISO8601')
cutoff = now - pd.Timedelta(hours=24)
last24df = df[df['timestamp'] >= cutoff]

@ui.page('/', title="Dashboard | How is MCO Today")
def main():
    global plot_element

    ui.label(f"Last updated: {latest['timestamp']}").classes('italic w-full text-center')

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
                    ui.label(f"{latest['cancelled']}").classes('text-5xl font-semibold')
                    ui.label('flights').classes('text-sm text-black-600')
                    ui.label('(comparison text)').classes('text-sm text-green-600')
            # Most Cancellations
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Most Cancellations').classes('text-xl')
                with ui.column().classes('items-end'):
                    ui.label(f"{latest['most_cancelled']}").classes('text-5xl font-semibold')

        with ui.column().classes('items-end ml-20'):
            # Number of Delays
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Delayed Flights').classes('text-xl')
                with ui.column().classes('items-end'):
                    ui.label(f"{latest['delayed']}").classes('text-5xl font-semibold')
                    ui.label('flights').classes('text-sm text-black-600')
                    ui.label('(comparison text)').classes('text-sm text-green-600')
            # Most Delays
            with ui.row().classes('items-baseline gap-4'):
                ui.label('Most Delays').classes('text-xl')
                with ui.column().classes('items-end'):
                    ui.label(f"{latest['most_delayed']}").classes('text-5xl font-semibold')

    with ui.column().classes('w-full items-center justify-center'):
        with ui.row(wrap=True).classes('w-full'):

            with ui.column().classes('flex-[2] items-center justify-center'):

                ui.label("Operational Trends").classes('text-2xl font-semibold')

                
            with ui.column().classes('flex-[1] items-center justify-center'):

                ui.label("TSA Waits").classes('text-2xl font-semibold')
                ui.label("plot here")

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