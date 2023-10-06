"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Songs Page of the Acoustic Print web app
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
    st.set_page_config(
        layout="wide", page_title="Acoustic Print - Songs", page_icon="🎵"
    )

    st.write("Hello world")

    # TODO
    # 2-3 columns - acoustic print, spider chart (song vs. genre vs. current selection), and bars (song vs. genre vs. current_)
    # progress bar
    # filterable
    # table with all tracks

    # define for song table
    with st.sidebar:
        st.write("Song Filters")
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.caption("Rhythm & Dynamics")
            min_valence, max_valence = st.slider(
                label="Valence",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="valence_filter",
            )
            min_energy, max_energy = st.slider(
                label="Energy",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="energy_filter",
            )
            min_dance, max_dance = st.slider(
                label="Danceability",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="dance_filter",
            )
        with col2:
            st.caption("Articulation & Texture")
            min_acoustics, max_acoustics = st.slider(
                label="Acousticness",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="acoustic_filter",
            )
            min_instrument, max_instrument = st.slider(
                label="Instrumentalness",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="instrument_filter",
            )
            min_speech, max_speech = st.slider(
                label="Speechiness",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="speech_filter",
            )

        st.caption("General Characteristics")
        min_live, max_live = st.slider(
            label="Liveness",
            min_value=0.0,
            max_value=1.0,
            value=[0.0, 1.0],
            key="live_filter",
        )
        min_tempo, max_tempo = st.slider(
            label="Tempo",
            min_value=12.0,
            max_value=275.0,
            value=[12.0, 275.0],
            key="tempo_filter",
        )
        explicit_vals = st.multiselect(
            label="Explict",
            options=(0, -1, 1),
            default=(0, -1, 1),
            format_func=lambda x: "Unknown" if x == -1 else "No" if x == 0 else "Yes",
        )
        min_duration, max_duration = st.slider(
            label="Duration (mins)",
            min_value=0.0,
            max_value=60.0,
            value=[0.0, 60.0],
            key="duration_filter",
        )

    # create database connection
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

    # query database for all tracks
    tracks_df = conn.query(
        """
        SELECT T.title AS Song, AR.name AS `Artist`, AB.title AS `Album Title`, 
            T.duration AS Duration, T.listens AS Listens, G.title AS Genre,
            T.valence AS Valence, T.energy AS Energy, T.danceability AS Danceability,
            T.acousticness AS Acousticness, T.instrumentalness AS Instrumentalness, T.speechiness AS Speechiness,
            T.liveness AS Liveness, T.tempo AS Tempo, T.explicit AS Explicit
        FROM Tracks T
            LEFT JOIN Albums AB ON T.album_id=AB.id
            INNER JOIN Artists AR ON T.artist_id=AR.id
            INNER JOIN Track_Genres TG ON T.id=TG.track_id
            INNER JOIN Genres G ON TG.genre_id=G.id
        ORDER BY Genre;
        """
    )

    # subset tracks with filters provided by user
    filtered_tracks_df = tracks_df.loc[
        (
            (min_valence <= tracks_df["Valence"])
            & (tracks_df["Valence"] <= max_valence)
            & (min_energy <= tracks_df["Energy"])
            & (tracks_df["Energy"] <= max_energy)
            & (min_dance <= tracks_df["Danceability"])
            & (tracks_df["Danceability"] <= max_dance)
            & (min_acoustics <= tracks_df["Acousticness"])
            & (tracks_df["Acousticness"] <= max_acoustics)
            & (min_instrument <= tracks_df["Instrumentalness"])
            & (tracks_df["Instrumentalness"] <= max_instrument)
            & (min_speech <= tracks_df["Speechiness"])
            & (tracks_df["Speechiness"] <= max_speech)
            & (min_live <= tracks_df["Liveness"])
            & (tracks_df["Liveness"] <= max_live)
            & (min_tempo <= tracks_df["Tempo"])
            & (tracks_df["Tempo"] <= max_tempo)
            & ((min_duration * 60) <= tracks_df["Duration"])
            & (tracks_df["Duration"] <= (max_duration * 60))
            & (tracks_df.Explicit.isin(explicit_vals))
        ),
        :,
    ].iloc[:, :-1]
    filtered_tracks_df["Duration"] = filtered_tracks_df.Duration.apply(
        lambda x: f"{x//60}:{x-((x//60)*60):02d}"
    )

    # # on page load, select a song
    # song_selection = None
    # if "song_selection" not in st.session_state:
    #     song_selection = np.random.randint(0, 2, 1)

    # # define visualizations
    # tab1, tab2, tab3 = st.tabs(["Acoustic-Print", "Radar", "Bar"])
    # with tab1:
    #     # Acoustic-print
    #     if not song_selection:
    #         st.empty()
    #         st.write("Please select a song")
    #     else:
    #         st.write("Acoustic-Print Here")

    # with tab2:
    #     # Radar chart
    #     if not song_selection:
    #         st.empty()
    #         st.write("Please select a song")
    #     else:
    #         st.write("Radar Chart Here")

    # with tab3:
    #     # Bar chart
    #     if not song_selection:
    #         st.empty()
    #         st.write("Please select a song")
    #     else:
    #         st.write("Bar Chart Here")

    # # define song selection widget
    # song_selection = st.multiselect(
    #     label="Song",
    #     options=(0, -1, 1),
    #     default=song_selection,
    #     format_func=lambda x: "tracks_df.loc[tracks_df.id==x, 'title']"
    #     + " by "
    #     + "tracks_df.loc[tracks_df.id==x, 'name']",
    #     max_selections=1,
    #     key="song_selection",
    # )

    # define table of tracks
    st.caption(body="Tracks", help="cmd+f/ctrl+f to search table")
    st.dataframe(
        filtered_tracks_df,
        hide_index=True,
        use_container_width=True,
    )


# main program
if __name__ == "__main__":
    main()
