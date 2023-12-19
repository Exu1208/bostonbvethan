"""
Name: Ethan Xu
CS230: Section 5
Data: Boston Building Violations
URL:

Description:

This program is a data analysis on a 7,000 record sample from the Boston Building Violations file. It Examines the
building violations in Boston by various criterion such as reason, neighborhood, time of day, and status.
"""

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import matplotlib.pyplot as plt

# Set app configuration and headers
st.set_page_config(layout="wide", page_title="Boston Building Violations", page_icon=":city_sunrise:")

st.title("Boston Building Violations Data Analysis")
st.write(
            """
        ## 
        Examining the building violations in Boston by various criterion such as reason, neighborhood, time of day, and 
        status. The data used in this app comes from a 7,000 building violation sample, based on the data resource 
        provided by the Building and Structures Division of the Inspectional Services Department.
        """
        )
st.caption("~An app by Ethan Xu")

# Define tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Data Analysis", "Mapping"])

with tab1:
    row1_1, row1_2 = st.columns((3, 2))
    with row1_1:
        st.title("Violations Overview")
    st.divider()
    row2_1, row2_2 = st.columns((3, 2))
    row3_1, row3_2 = st.columns((99, 1))
    row4_1, row4_2 = st.columns((99, 1))

# Gather and customize relevant data from original file
def load_data():
    path = "boston_building_violations_7000_sample.csv"

    data = pd.read_csv(
        path,
        nrows=7000,
        names=[
            "Violation ID",
            "date/time",
            "Status",
            "Reason",
            "Violation Neighborhood",
            "Latitude",
            "Longitude",
        ],
        skiprows=1,
        usecols=[0, 1, 2, 5, 10, 20, 21],

    )
    data["date/time"] = pd.to_datetime(data["date/time"], format="%m/%d/%Y %H:%M", errors="coerce")
    return data

df = pd.read_csv("boston_building_violations_7000_sample.csv")

violation_city = "violation_city"

violations_by_city = df.groupby(violation_city).size().reset_index(name='Number of Violations')

# Create chart of violations by neighborhoods
with row2_1:
    chart = alt.Chart(violations_by_city).mark_bar().encode(
        x=alt.X(violation_city, title="Boston Neighborhoods"),
        y=alt.Y('Number of Violations', title="# of Violations"),
        tooltip=[violation_city, 'Number of Violations']
    ).properties(
        title="Building Violations in Boston Neighborhoods"
    )

    st.altair_chart(chart)

violation_status = "status"

violations_by_status = df.groupby(violation_status).size().reset_index(name='Number of Violations')

# Create chart by status
with row2_2:
    chart = alt.Chart(violations_by_status).mark_bar(color='red').encode(
        y=alt.Y(violation_status, title="Violation Reasons"),
        x=alt.X('Number of Violations', title="# of Violations"),
        tooltip=[violation_status, 'Number of Violations']
    ).properties(
        title="Building Violations by Status"
    )

    st.altair_chart(chart)

st.divider()
data = load_data()

with row3_1:
    st.subheader("Below is the table of raw data, including the relevant columns used in this data analysis.")
    st.write(data)

    st.divider()

# Create pie chart
with row4_1:
    nei_violation_counts = data.groupby("Violation Neighborhood")["Violation ID"].count().reset_index()
    nei_violation_counts.columns = ["Neighborhood", "Total Violations"]
    total_violations = nei_violation_counts["Total Violations"].sum()

    fig, ax = plt.subplots()
    ax.pie(nei_violation_counts["Total Violations"], labels=nei_violation_counts["Neighborhood"],
           autopct='',  # Only display percentages in the pie chart
           startangle=90, counterclock=False)

    st.pyplot(fig)

    nei_violation_counts["Percentage"] = nei_violation_counts["Total Violations"] / total_violations * 100

    st.subheader("Total Violations and Percentages by Neighborhood")
    formatted_table = nei_violation_counts[["Neighborhood", "Total Violations", "Percentage"]].copy()
    formatted_table["Percentage"] = formatted_table["Percentage"].round(1).astype(str) + '%'
    st.table(formatted_table)

with tab2:
    row1_1, row1_2 = st.columns((1, 4))
    row2_1, row2_2 = st.columns((2, 2))

    # Create dropdown select widget that links to graphs below
    with row1_1:
        neighborhood_column = "violation_city"
        reasons_column = "description"
        status_column = 'status'
        neighborhood_options = df[neighborhood_column].unique()
        selected_neighborhood = st.selectbox("Select Neighborhood", neighborhood_options)
        filtered_df = df[df[neighborhood_column] == selected_neighborhood]

    # Create chart by reasons dependent on user selected neighborhood
    with row2_1:
        reasons_chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X(reasons_column, title="Reasons for Violations"),
            y=alt.Y('count()', title="# of Violations"),
            tooltip=[reasons_column, 'count()']
        ).properties(
            title=f"Violations by Reason in {selected_neighborhood}"
        )

    # Create chart by status dependent on user selected neighborhood
    with row2_2:
        status_chart = alt.Chart(filtered_df).mark_bar(color='red').encode(
            x=alt.X(status_column, title="Violation Status"),
            y=alt.Y('count()', title="# of Violations"),
            tooltip=[status_column, 'count()']
        ).properties(
            title=f"Violations Status in {selected_neighborhood}"
        )

    st.altair_chart(reasons_chart, use_container_width=True)
    st.altair_chart(status_chart, use_container_width=True)

# Define location of Boston
boston = [42.36, -71.06]

# Set map parameters
def map(data, lat, lon, zoom):
    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "pitch": 50,
            },
            tooltip={
                "html": "<b>Violations:</b> {elevationValue}",
                "style": {
                    "backgroundColor": "steelblue",
                    "color": "white"
                }
            },
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=data,
                    get_position=["Longitude", "Latitude"],
                    radius=100,
                    elevation_scale=4,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=True,

                ),
            ],
        )
    )

# Filter imported data by hour of the day
def filterdata(df, hour_selected):
    return df[df["date/time"].dt.hour == hour_selected]

if not st.session_state.get("url_sync", False):
    try:
        violation_hour = int(st.experimental_get_query_params()["violation_hour"][0])
        st.session_state["violation_hour"] = violation_hour
        st.session_state["url_sync"] = True
    except KeyError:
        pass


# Updates query parameters if the slider changes value
def update_query_params():
    hour_selected = st.session_state["violation_hour"]
    st.experimental_set_query_params(violation_hour=hour_selected)

with tab3:
    row1_1, row1_2 = st.columns((2, 3))
    row2_1, row2_2 = st.columns((99, 1))
    with row1_1:
        hour_selected = st.slider(
            "Select hour of day", 0, 23, key="violation_hour", on_change=update_query_params
        )

    # Generate map
    with row2_1:
        st.write(
            f"""**Boston building violations occurred from {hour_selected}:00 to {(hour_selected + 1) % 24}:00**"""
        )
        map(filterdata(data, hour_selected), boston[0], boston[1], 11)

    st.caption('This map shows where the building violations occur at in each hour of the day. Please use the slider to select an hour during the day and the map will alter accordingly.')