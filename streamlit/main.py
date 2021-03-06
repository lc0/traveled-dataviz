import json
import os

import altair as alt
import foursquare
import pandas as pd
import streamlit as st


from datetime import datetime
from typing import List


# @st.cache()
def get_foursquare_data(foursquare_token):

    # TODO: move it to another wrapper
    # TODO: check the lifecycle of streamlit
    cache_filename = 'foursquare.cache'

    if os.path.exists(cache_filename):
        print('loading from local cache')

        with open(cache_filename) as cache_file:
            cached = json.load(cache_file)

            return cached
    else:
        print('loading not cached version')

    client = foursquare.Foursquare(access_token=foursquare_token)
    all_checkins = client.users.all_checkins()

    print("I hope we do not read this over and over")

    processed = [{'country': checkin['venue']['location']['country'],
                  'city': checkin['venue']['location'].get('city', 'None'),
                  'lat': checkin['venue']['location']['lat'],
                  'lng': checkin['venue']['location']['lng'],
                  'visited_at': checkin['createdAt'],
                  'location': checkin['venue']['name']
                 } for checkin in all_checkins]

    with open(cache_filename, 'w') as cache_file:
        json.dump(processed, cache_file)

        print("Just dumped file to cache")

    return processed

def sidebar_ui(checkins_df):
    st.sidebar.markdown("# the most places")
    places_number = st.sidebar.slider("How many places preview?", min_value=1, max_value=10, value=3)

    shown_columns = st.sidebar.multiselect("What columns of data should be shown?",
                                            options=list(checkins_df.columns),
                                            default=['country', 'city', 'lng', 'lat', 'location'])

    return places_number, shown_columns


def compute_new_countries(dataframe) -> pd.DataFrame:
    dataframe['ones'] = 1
    dataframe['visited_time'] = dataframe.sort_values(['visited_at'], ascending=[True]).groupby(['country'])['ones'].cumsum()

    new_countries_visited = dataframe[dataframe['visited_time'] == 1]

    return new_countries_visited


def get_total_stats(checkins_df):
    all_visited_places = alt.Chart(checkins_df).mark_bar().encode(
        x=alt.X('year:N'),
        y=alt.Y('distinct(location)', title="Distinct location"),
        color='country',
        tooltip=['country', 'distinct(location)']
    )

    all_checkins = alt.Chart(checkins_df).mark_line().encode(
        x=alt.X('year:N'),
        y=alt.Y('count()', title="Total checkins"),
        tooltip=['count()']
    )

    return (all_visited_places + all_checkins).properties(width=700)

def get_visited_map(checkins_df, new_countries):
    from vega_datasets import data

    vega_countries = alt.topo_feature(data.world_110m.url, 'countries')

    selection = alt.selection_multi(fields=['year'])
    color = alt.condition(selection,
                        alt.Color('year:N', legend=None),
                        alt.value('lightgray'))

    size = alt.condition(selection,
                        alt.value(200),
                        alt.value(10))

    base = alt.Chart(vega_countries).mark_geoshape(
        # fill='#666666',
        # stroke='white'
    ).project('mercator')

    points = alt.Chart(checkins_df).mark_circle(
        opacity=0.5,
        size=20
    ).encode(
        longitude='lng:Q',
        latitude='lat:Q',
        tooltip=['city', 'country', 'year'],
        color=color,
        size=size
    ).properties(width=400, title="wtf")

    legend = alt.Chart(checkins_df).mark_bar().encode(
        y=alt.Y('year:N'),
        color=color
    ).add_selection(
        selection
    ).properties(title="works here", width=30)

    country_list = alt.Chart(checkins_df).mark_text(
    ).transform_filter(
        selection
    ).encode(
        y=alt.Y('country:N', title='Visited countries')
    )

    new_countries_list = alt.Chart(new_countries).mark_text(
    ).transform_filter(
        selection
    ).transform_calculate(
        county_and_month='datum.country + " on " + datum.visited_date'
    ).encode(
        y=alt.Y('county_and_month:N', title='Fist time visited ')
    )

    return (base + points) | (legend | country_list | new_countries_list)


def main():
    try:
        FOURSQUARE_TOKEN = os.environ['FOURSQUARE']
    except KeyError:
        raise ValueError("""Please provide `FOURSQUARE` as an environment variable.
    For more details: please check the installation section of the readme file.""")

    st.title('🌍Places traveled')

    foursquare_data = get_foursquare_data(FOURSQUARE_TOKEN)
    checkins_df = pd.DataFrame.from_dict(foursquare_data)

    st.markdown("The tracked data with Foursquare")
    st.dataframe(checkins_df)

    checkins_df['visited_date'] = checkins_df.apply(lambda x: datetime.fromtimestamp(x['visited_at']), axis=1)
    checkins_df['year'] = checkins_df.apply(lambda x: x['visited_date'].year, axis=1)
    checkins_df['month'] = checkins_df.apply(lambda x: x['visited_date'].month, axis=1)

    st.markdown("### 🧮 These checkins were made in ..")
    total_stats = get_total_stats(checkins_df)
    st.altair_chart(total_stats)

    most_limit, shown_columns = sidebar_ui(checkins_df)
    st.markdown("## 🧭 The most checkins")
    try:
        st.markdown("### The most South point")
        st.dataframe(checkins_df[shown_columns].sort_values(by=['lat']).head(most_limit))
        st.markdown("### The most North point")
        st.dataframe(checkins_df[shown_columns].sort_values(by=['lat'], ascending=False).head(most_limit))
    except KeyError:
        st.error('`lat` column is required to define the most East and West points')

    try:
        st.markdown("### The most West point")
        st.dataframe(checkins_df[shown_columns].sort_values(by=['lng']).head(most_limit))
        st.markdown("### The most East point")
        st.dataframe(checkins_df[shown_columns].sort_values(by=['lng'], ascending=False).head(most_limit))
    except KeyError:
        st.error('`lng` column is required to define the most East and West points')


    new_countries_visited = compute_new_countries(checkins_df)
    st.markdown("## 🇺🇳 New countries visited each year ")
    st.dataframe(new_countries_visited[['year', 'country', 'city', 'visited_date', 'location']])


    new_countries = alt.Chart(new_countries_visited).mark_bar(
    ).encode(
        x=alt.X('year:N'),
        y=alt.Y('distinct(country)'),
        color='country',
        tooltip=['country', 'location']
    ).properties(width=700)
    st.markdown("Let's see how many **new** countries were visited each year")
    st.altair_chart(new_countries)

    st.markdown("## 🗺 Location by year - interactive map")
    st.altair_chart(get_visited_map(checkins_df, new_countries_visited), use_container_width=True)


if __name__ == "__main__":
    main()