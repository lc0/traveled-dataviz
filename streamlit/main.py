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
    import os.path
    import json

    if os.path.exists(cache_filename):
        print('loading from local cache')

        with open(cache_filename) as cache_file:
            cached = json.load(cache_file)

            return cached
    else:
        print('loading not cached version')

    client = foursquare.Foursquare(access_token=foursquare_token)
    all_checkins = client.users.all_checkins()
    # all_checkins = client.users.checkins()

    print(all_checkins)
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

def get_visited_map(checkins_df):
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
    ).properties(
        # width=800,
        # height=800
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
    )

    legend = alt.Chart(checkins_df).mark_bar().encode(
        y=alt.Y('year:N', axis=alt.Axis(orient='right')),
        color=color
    ).add_selection(
        selection
    )

    country_list = alt.Chart(checkins_df).mark_bar(

    ).transform_filter(
        selection
    ).encode(
        y='country:N',
    )

    return (base + points) | legend | country_list


def main():
    try:
        FOURSQUARE_TOKEN = os.environ['FOURSQUARE']
    except KeyError:
        raise ValueError("""Please provide `FOURSQUARE_TOKEN` as an environment variable.
    For more details: please check the installation section of the readme file.""")

    st.title('🌍Places traveled')

    foursquare_data = get_foursquare_data(FOURSQUARE_TOKEN)
    checkins_df = pd.DataFrame.from_dict(foursquare_data)

    st.markdown("The tracked data with Foursquare")
    st.dataframe(checkins_df)

    MOST_LIMIT = 3
    st.markdown("## The most checkins")
    st.markdown("### The most South")
    st.dataframe(checkins_df.sort_values(by=['lat']).head(MOST_LIMIT))

    st.markdown("### The most North")
    st.dataframe(checkins_df.sort_values(by=['lat'], ascending=False).head(MOST_LIMIT))

    st.markdown("### The most West")
    st.dataframe(checkins_df.sort_values(by=['lng']).head(MOST_LIMIT))

    st.markdown("### The most East")
    st.dataframe(checkins_df.sort_values(by=['lng'], ascending=False).head(MOST_LIMIT))


    checkins_df['visited_date'] = checkins_df.apply(lambda x: datetime.fromtimestamp(x['visited_at']), axis=1)
    checkins_df['year'] = checkins_df.apply(lambda x: x['visited_date'].year, axis=1)
    checkins_df['month'] = checkins_df.apply(lambda x: x['visited_date'].month, axis=1)

    # TODO: move to a function
    checkins_df['ones'] = 1
    checkins_df['visited_time'] = checkins_df.sort_values(['visited_at'], ascending=[True]).groupby(['country'])['ones'].cumsum()

    new_countries_visited = checkins_df[checkins_df['visited_time'] == 1]
    st.markdown("### New countries visited each year")
    st.dataframe(new_countries_visited[['year', 'country', 'city', 'visited_date', 'location']])


    new_countries = alt.Chart(new_countries_visited).mark_bar(
    ).encode(
        x=alt.X('year:N'),
        y=alt.Y('distinct(country)'),
        color='country',
        tooltip=['country', 'location']
    )
    st.markdown("Let's see how many **new** countries were visited each year")
    st.altair_chart(new_countries)

    st.markdown("Location by year - interactive map")
    st.altair_chart(get_visited_map(checkins_df), width=-1)


if __name__ == "__main__":
    main()