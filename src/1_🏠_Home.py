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
    get_audio_descriptions,
    get_sql_connect_str,
    plot_acoustic_print,
)


def main():
    # define local page config
    st.set_page_config(layout="wide", page_title="Acoustic Print - Home", page_icon="🏠")

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
        An audio or acoustic fingerprint is a digital summary that can be generated from an audio signal deterministically. 
        Generally, it allows for the lookup of similar audio signals and helps identify an audio signal so it can be 
        recognized quickly later. 
        
        **Acoustic-Print** is a project that seeks to develop a visual representation of an acoustic fingerprint with a similar 
        foundation in mind; the acoustic fingerprint should be deterministic and songs that are similar in audio features should
        have similar acoustic-prints. The acoustic-print of a song is split into two visualizations, one representing Rhythm & Dynamics
        (comprised of valence, energy, and danceability) and the other Articulation & Texture (comprised of speechiness, instrumentalness, 
        and acousticness), with embedding information about the tempo of the song.
        """
    )

    feature_desc = get_audio_descriptions()
    with st.expander("See further details"):
        # TODO - Write stuff about data and analyss
        st.write(
            f"""
            ### Analysis
            Stuff about data and analysis ... [PLACEHOLDER] Polar Curves

            ### Audio Features
            | Audio feature       | Description        |
            |---------------------|--------------------|
            | Valence             | {feature_desc[0]}  |
            | Energy              | {feature_desc[1]}  |
            | Danceability        | {feature_desc[2]}  |
            | Acousticness        | {feature_desc[3]}  |
            | Instrumentalness    | {feature_desc[4]}  |
            | Speechiness         | {feature_desc[5]}  |
            | Tempo               | {feature_desc[6]}  |
            | Liveness            | {feature_desc[7]}  |
            
            ### Data
            [PLACEHOLDER]
            """
        )
    st.divider()

    # query database for random track
    rand_song = conn.query(
        """
        SELECT title AS `Song`, acousticness AS Acousticness, danceability AS Danceability, 
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
        SELECT Ab.id, Ab.title AS Album, Ab.release_date AS `Release Date`,
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
        column_order=("Album", "Artist", "Release Date", "Favorites", "Listens"),
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
                ["artist_id", "Album"],
            ],
            left_on="id",
            right_on="artist_id",
            how="inner",
        ),
        hide_index=True,
        use_container_width=True,
        column_order=("Artist", "Favorites", "Number of Albums", "Album"),
        column_config={"Album": "Most Popular Album"},
    )


# main program
if __name__ == "__main__":
    main()
