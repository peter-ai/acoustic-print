"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Home Page of the Acoustic Print web app
"""
# import external dependencies
import numpy as np
import pandas as pd
import streamlit as st

# import user defined package
from acoustic_helpers import (
    generate_fingerprint,
    get_sql_connect_str,
    plot_acoustic_print,
)


def main():
    # define local page config
    st.set_page_config(layout="wide", page_title="Acoustic Print - Home", page_icon="🏠")
    st.sidebar.write("ON HOME PAGE DELETE IF NOT NEEDED")

    # create database connection
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

    # start page
    # TODO Project Description
    st.title("Acoustic-Print")
    st.write(
        """
        **Author: Peter Akioyamen** (see [@peter-ai](https://github.com/peter-ai/acoustic-print) for the full github repo)
        
        ### Context
        Acoustic-Print is a project that seeks to ... [PLACEHOLDER]
        """
    )
    with st.expander("See a details about data and analysis"):
        st.write(
            """
            Stuff about data and analysis ... [PLACEHOLDER]
            """
        )
    st.divider()

    # query database for random track
    rand_song = conn.query(
        """
        SELECT title AS Name, acousticness AS Acousticness, danceability AS Danceability, 
            valence AS Valence, energy AS Energy, tempo AS Tempo, speechiness AS Speechiness, 
            instrumentalness AS Instrumentalness, name AS Artist 
        FROM Tracks 
            INNER JOIN Artists ON Tracks.artist_id=Artists.id
        ORDER BY RAND()
        LIMIT 1;
        """,
        ttl=1000,
    )
    DY_df = generate_fingerprint(rand_song, category="dynamics")
    AR_df = generate_fingerprint(rand_song, points=2000, category="articulation")
    plot_acoustic_print(rand_song, DY_df, AR_df)

    # query database for albums data
    albums_df = conn.query(
        """ 
        SELECT Ab.id, Ab.title AS `Album Title`, Ab.release_date AS `Release Date`,
            Ab.favorites AS Favorites, Ab.listens AS Listens, Ar.name AS Artist, Ab.artist_id
        FROM Albums Ab
            INNER JOIN Artists Ar
                ON Ab.artist_id=Ar.id
        WHERE Ab.num_tracks<>0 AND Ab.release_date IS NOT NULL;
        """
    )
    # format and display albums data
    st.caption(body="Albums", help="cmd+f/ctrl+f to search table")
    st.dataframe(
        albums_df,
        hide_index=True,
        use_container_width=True,
        column_order=("Album Title", "Artist", "Release Date", "Favorites", "Listens"),
    )

    # query database for artists data
    artists_df = conn.query(
        """ 
        SELECT Ar.id, Ar.name as Artist, Ar.favorites AS Favorites, COUNT(Ab.id) AS `Number of Albums`
        FROM Artists Ar
            INNER JOIN Albums Ab
                ON Ab.artist_id=Ar.id
        WHERE Ab.num_tracks<>0 AND Ab.release_date IS NOT NULL
        GROUP BY Ar.id, Ar.name, Ar.favorites;
        """
    )

    # format and display artists data
    st.caption(body="Artists", help="cmd+f/ctrl+f to search table")
    st.dataframe(
        pd.merge(
            left=artists_df,
            right=albums_df.loc[
                albums_df.groupby(by="Artist")["Favorites"].idxmax(),
                ["artist_id", "Album Title"],
            ],
            left_on="id",
            right_on="artist_id",
            how="inner",
        ),
        hide_index=True,
        use_container_width=True,
        column_order=("Artist", "Favorites", "Number of Albums", "Album Title"),
        column_config={"Album Title": "Most Popular Album"},
    )


# main program
if __name__ == "__main__":
    main()
