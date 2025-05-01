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
#import _downloaddata
from datetime import datetime

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


@ui.page('/', title="Dashboard | How is MCO Today", dark=True)
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
        #plot.update()
        cancelledcount.set_text(f"{latest['cancelled']}")
        delayedcount.set_text(f"{latest['delayed']}")
        mostcancelled.set_text(f"{latest['most_cancelled']}")
        mostdelayed.set_text(f"{latest['most_delayed']}")
        timestamp_dt = datetime.fromisoformat(latest['timestamp'])
        formatted_date = timestamp_dt.strftime('%a. %B %d %Y @ %I:%M %p')
        lastupdated.set_text(f"Last updated: {formatted_date}")
        totalcount.set_text(f"{latest['total_flights']}")
        render_tsa_cards()
        render_atc_advisories()
        refresh_plot()
        render_other_parking_cards()
        render_regular_parking_cards()
        ui.notification(message="Refreshed!", timeout=3)
        
    with ui.row().classes('items-center justify-center w-full'):
        timestamp_dt = datetime.fromisoformat(latest['timestamp'])
        formatted_date = timestamp_dt.strftime('%a. %B %d %Y @ %I:%M %p')
        lastupdated = ui.label(f"Last updated: {formatted_date}").classes('italic')
        ui.button('Update data', on_click=lambda: update_data())

    ui.separator().classes('mb-5')

    with ui.row().classes('items-center justify-center w-full'):
        with ui.column().classes('items-start'):
            ui.label('How is MCO').classes('text-5xl font-light')
            ui.label('today?').classes('text-7xl font-bold text-black-900')
            ui.link('by Dariel Cruz Rodriguez', 'https://dariel.us').classes('text-sm mt-4 inline')
            with ui.button('Sponsor This Project', on_click=lambda: ui.run_javascript('window.open("https://ko-fi.com/darielc")')).classes('bg-green'):
                ui.tooltip('Thank you for supporting my work! <3').classes('bg-black')
        with ui.row().classes('items-start justify-center ml-20 space-x-10'):
            with ui.column().classes('items-start'):
                # Cancelled Flights Metric
                ui.label('Total Flights').classes('text-xl')
                totalcount = ui.label(f"{latest['total_flights']}").classes('text-5xl font-semibold')
                ui.label('flights').classes('text-sm text-black-600')
                #ui.label('(comparison text)').classes('text-sm text-green-600')
            with ui.column().classes('items-start'):
                # Cancelled Flights Metric
                ui.label('Cancelled Flights').classes('text-xl')
                cancelledcount = ui.label(f"{latest['cancelled']}").classes('text-5xl font-semibold')
                ui.label('flights').classes('text-sm text-black-600')
                #ui.label('(comparison text)').classes('text-sm text-green-600')
            with ui.column().classes('items-start'):
                # Delayed Flights Metric
                ui.label('Delayed Flights').classes('text-xl')
                delayedcount = ui.label(f"{latest['delayed']}").classes('text-5xl font-semibold')
                ui.label('flights').classes('text-sm text-black-600')
                #ui.label('(comparison text)').classes('text-sm text-green-600')
            with ui.column().classes('items-start'):
                # Most Cancellations Metric
                ui.label('Most Cancellations').classes('text-xl')
                mostcancelled = ui.label(f"{latest['most_cancelled']}").classes('text-5xl font-semibold')
            with ui.column().classes('items-start'):
                # Most Delays Metric
                ui.label('Most Delays').classes('text-xl')
                mostdelayed = ui.label(f"{latest['most_delayed']}").classes('text-5xl font-semibold')

    ui.element('div').style('height: 10%;')

    with ui.column().classes('w-full items-center justify-center flex-wrap'):
        with ui.row(wrap=True).classes('w-full'):

            with ui.column().classes('md:w-[45%] items-center justify-center'):

                def refresh_plot():
                        data = _operationaltrends.get_params()
                        plot_container.clear()  # Clear previous plot
                        with plot_container:
                            ui.plotly(data).classes('w-full h-15')  # Recreate the plot with updated data

                ui.label("Operational Trends").classes('text-2xl font-semibold')

                plot_container = ui.column().classes("w-[90%] items-center")
                refresh_plot()

            with ui.column().classes('md:w-[25%] items-center justify-center'):

                ui.label("TSA Wait Times").classes('text-2xl font-semibold')
                waitsdf = util.get_security_waits()

                with ui.card().classes("w-full"):
                    ui.label(f"Overall Average Wait").classes('text-xl font-semibold')
                    averagewait = ui.label(f"Wait Time: {int(waitsdf['averagewait'].mean())} minutes")

                tsa_container_wrapper = ui.column().classes('w-full')  # This is where cards will go

                def render_tsa_cards():
                    tsa_container_wrapper.clear()

                    waitsdf = util.get_security_waits()
                    if len(waitsdf) <= 0:
                        with tsa_container_wrapper:
                            ui.label("Error fetching TSA wait times")
                        return

                    for _, lane in waitsdf.iterrows():
                        with tsa_container_wrapper:
                            with ui.card().classes("w-full"):
                                ui.label(f"{lane['name']}").classes('text-xl font-semibold')
                                ui.label(f"Wait Time: {int(lane['averagewait'])} minutes")

                render_tsa_cards()


            with ui.column().classes('md:w-[25%] items-center justify-center'):

                def render_atc_advisories():
                    atc_container.clear()
                    with atc_container:
                        airportcode = "MCO"
                        airport = Airport(airportcode)
                        airport.getDelays()

                        if airport.airportdelays is None:
                            ui.image("https://i.ibb.co/TBCbvjys/Untitled-design-53.png").classes('w-2/4 mx-auto')
                            ui.label("There are no active advisories.").classes('mx-auto text-center')
                            ui.label("Enjoy this picture of Violet the Cat. :)").classes('mx-auto text-center')
                        else:
                            for key, value in airport.airportdelays.items():
                                ui.chat_message(
                                    f"There is a delay on {airportcode} <strong>{key}s</strong> averaging <strong>{value['avgDelay']} minutes</strong> \
                                        (btwn. {value['minDelay']}-{value['maxDelay']} min) due to <strong>{value['reason']}</strong>.",
                                    text_html=True,
                                    name='Air Traffic Control',
                                    stamp=None,
                                    avatar='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Seal_of_the_United_States_Federal_Aviation_Administration.svg/1200px-Seal_of_the_United_States_Federal_Aviation_Administration.svg.png'
                                )

                ui.label("Active ATC Advisories").classes('text-2xl font-semibold text-center')
                atc_container = ui.column().classes("w-full")
                render_atc_advisories()
    ####

    ui.element('div').style('height: 10%;')
    
    ####

    with ui.column().classes('w-full items-center justify-center flex-wrap'):
        with ui.row(wrap=True).classes('w-full'):

            with ui.column().classes('md:w-[31%] items-center justify-center'):

                ui.label("Parking Status").classes('text-2xl font-semibold')

                with ui.tabs().classes('w-full') as tabs:
                    one = ui.tab('Regular Garages')
                    two = ui.tab('Other Garages')
                with ui.tab_panels(tabs, value=one).classes('w-full'):

                    with ui.tab_panel(one):
                        def render_regular_parking_cards():
                            parking_container_reg_wrapper.clear()
                            parkingdf = util.get_parking_loads()
                            parkingdf = parkingdf[parkingdf['category'].isin(['garage'])]
                            if len(parkingdf) <= 0:
                                with parking_container_reg_wrapper:
                                    ui.label("Error fetching TSA wait times")
                                return
                            for _, garage in parkingdf.iterrows():
                                with parking_container_reg_wrapper:
                                    with ui.card().classes("w-full " + ("bg-green-700" if garage['status'].lower() == "open" else "bg-red-700")):
                                        ui.label(f"{garage['garagename']}").classes('text-xl font-semibold')
                                        ui.label(f"Status: {garage['status']}")
                        
                        parking_container_reg_wrapper = ui.column().classes('w-full')  # This is where cards will go
                        render_regular_parking_cards()
                    
                    with ui.tab_panel(two):
                        with ui.scroll_area().classes('w-full h-100'):
                            def render_other_parking_cards():
                                parking_container_other_wrapper.clear()
                                parkingdf_other = util.get_parking_loads()
                                parkingdf_other = parkingdf_other[~parkingdf_other['category'].isin(['garage'])]
                                if len(parkingdf_other) <= 0:
                                    with parking_container_other_wrapper:
                                        ui.label("Error fetching TSA wait times")
                                    return
                                for _, garage in parkingdf_other.iterrows():
                                    with parking_container_other_wrapper:
                                        with ui.card().classes("w-full " + ("bg-green-700" if garage['status'].lower() == "open" else "bg-red-700")):
                                            ui.label(f"{garage['garagename']}").classes('text-xl font-semibold')
                                            ui.label(f"Status: {garage['status']}")
                            
                            parking_container_other_wrapper = ui.column().classes('w-full')  # This is where cards will go
                            render_other_parking_cards()

                #parkingdetails = ui.column().classes("w-[90%] items-center")


            with ui.column().classes('md:w-[33%] items-center justify-center'):

                ui.label("Delay Counts by Airline").classes('text-2xl font-semibold')

            with ui.column().classes('md:w-[33%] items-center justify-center'):

                ui.label("Cancellation Counts by Airline").classes('text-2xl font-semibold')
####

ui.run(port=5001)