import os

import altair as alt
import foursquare
import pandas as pd
import streamlit as st


from datetime import datetime
from typing import List


@st.cache()
def get_foursquare_data(foursquare_token):
    client = foursquare.Foursquare(access_token=foursquare_token)
    all_checkins = client.users.all_checkins()

    print(all_checkins)
    print("I hope we do not read this over and over")

    processed = [{'country': checkin['venue']['location']['country'], 
                  'city': checkin['venue']['location'].get('city', 'None'),
                  'lat': checkin['venue']['location']['lat'],
                  'lng': checkin['venue']['location']['lng'],
                  'visited_at': checkin['createdAt'],
                  'location': checkin['venue']['name']
                 } for checkin in all_checkins]

    return processed


def main():
    try:
        FOURSQUARE_TOKEN = os.environ['FOURSQUARE']
    except KeyError:
        raise ValueError("""Please provide `FOURSQUARE_TOKEN` as an environment variable. 
    For more details: please check the installation section of the readme file.""")

    st.title('🌍Places traveled')

    foursquare_data = get_foursquare_data(FOURSQUARE_TOKEN)
    checkins_df = pd.DataFrame.from_dict(foursquare_data)

    st.markdown("The tracked data")
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
    st.markdown("Let's see how many new countries we visited per year")
    st.altair_chart(new_countries)
    


if __name__ == "__main__":
    main()