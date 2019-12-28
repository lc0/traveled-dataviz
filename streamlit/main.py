import os

import streamlit as st
import pandas as pd
import foursquare

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

    st.title('🤔 The best picture from duck place')

    foursquare_data = get_foursquare_data(FOURSQUARE_TOKEN)
    checkins_df = pd.DataFrame.from_dict(foursquare_data)

    st.dataframe(checkins_df.head())

    MOST_LIMIT = 5
    st.markdown("## The most checkins")
    st.markdown("### The most Sauth")
    st.dataframe(checkins_df.sort_values(by=['lat']).head(MOST_LIMIT))

    st.markdown("### The most North")
    st.dataframe(checkins_df.sort_values(by=['lat'], ascending=False).head(MOST_LIMIT))

    st.markdown("### The most North")
    st.dataframe(checkins_df.sort_values(by=['lat'], ascending=False).head(MOST_LIMIT))

    st.markdown("### The most West")
    st.dataframe(checkins_df.sort_values(by=['lng']).head(MOST_LIMIT))

    st.markdown("### The most East")
    st.dataframe(checkins_df.sort_values(by=['lng'], ascending=False).head(MOST_LIMIT))
    


if __name__ == "__main__":
    main()