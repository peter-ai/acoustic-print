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
    get_audio_descriptions,
    get_filtered_acoustics,
    get_sql_connect_str,
    plot_acoustic_print,
    plot_acoustic_radar,
)


def main():
    # define local page config
    st.set_page_config(
        layout="wide", page_title="Acoustic Print - Songs", page_icon="🎵"
    )

    # create audio feature description table
    feature_desc = get_audio_descriptions()
    with st.expander("Description of audio features"):
        st.caption("", help="double click description to expand details")
        st.dataframe(
            pd.DataFrame(
                {
                    "Audio feature": [
                        "Valence",
                        "Energy",
                        "Danceability",
                        "Acousticness",
                        "Instrumentalness",
                        "Speechiness",
                        "Tempo",
                        "Liveness",
                    ],
                    "Description": feature_desc,
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    # edit the display with of multiselect widgets
    st.markdown(
        """
    <style>
        .stMultiSelect [data-baseweb=select] span{
            max-width: 350px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    ### ------------------------------------------------------------------
    ### Define audio feature filters in sidebar
    with st.sidebar:
        st.write("Song Filters")
        col1, col2 = st.columns(2, gap="medium")

        # define left column as container
        with col1:
            st.caption("Rhythm & Dynamics")
            # filter for song valence
            min_valence, max_valence = st.slider(
                label="Valence",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="valence_filter",
            )

            # filter for song energy
            min_energy, max_energy = st.slider(
                label="Energy",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="energy_filter",
            )

            # filter for song danceability
            min_dance, max_dance = st.slider(
                label="Danceability",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="dance_filter",
            )

        # define right column as container
        with col2:
            st.caption("Articulation & Texture")

            # filter for song acousticness
            min_acoustics, max_acoustics = st.slider(
                label="Acousticness",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="acoustic_filter",
            )

            # filter for song instrumentalness
            min_instrument, max_instrument = st.slider(
                label="Instrumentalness",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="instrument_filter",
            )

            # filter for song speechiness
            min_speech, max_speech = st.slider(
                label="Speechiness",
                min_value=0.0,
                max_value=1.0,
                value=[0.0, 1.0],
                key="speech_filter",
            )

        st.caption("General Characteristics")
        # filter for song liveness
        min_live, max_live = st.slider(
            label="Liveness",
            min_value=0.0,
            max_value=1.0,
            value=[0.0, 1.0],
            key="live_filter",
        )

        # filter for song tempo
        min_tempo, max_tempo = st.slider(
            label="Tempo",
            min_value=12.0,
            max_value=275.0,
            value=[12.0, 275.0],
            key="tempo_filter",
        )

        # filter for length of song
        min_duration, max_duration = st.slider(
            label="Duration (mins)",
            min_value=0.0,
            max_value=60.0,
            value=[0.0, 60.0],
            key="duration_filter",
        )

        # filter for explicit songs
        explicit_vals = st.multiselect(
            label="Explict",
            options=(0, -1, 1),
            default=(0, -1, 1),
            format_func=lambda x: "Unknown" if x == -1 else "No" if x == 0 else "Yes",
        )

    ### ------------------------------------------------------------------
    ### Database connection and query
    # connect to database
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

    # query database for all tracks
    tracks_df = conn.query(
        """
        SELECT T.title AS `Song`, AR.name AS Artist, AB.title AS Album, 
            T.duration AS Duration, T.Favorites AS Favorites, T.listens AS Listens, G.title AS Genre,
            T.valence AS Valence, T.energy AS Energy, T.danceability AS Danceability,
            T.acousticness AS Acousticness, T.instrumentalness AS Instrumentalness, T.speechiness AS Speechiness,
            T.liveness AS Liveness, T.tempo AS Tempo, T.id, T.explicit AS Explicit
        FROM Tracks T
            LEFT JOIN Albums AB ON T.album_id=AB.id
            INNER JOIN Artists AR 
                ON T.artist_id=AR.id
            INNER JOIN Track_Genres TG 
                ON T.id=TG.track_id
            INNER JOIN Genres G 
                ON TG.genre_id=G.id
            ORDER BY Listens DESC;
        """
    )

    # filter table of tracks based on user provided parameters
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

    # seperate filtered data into subsets, one with the genre and and the other without
    filtered_genres_df = filtered_tracks_df.filter(
        [
            "id",
            "Valence",
            "Energy",
            "Danceability",
            "Acousticness",
            "Instrumentalness",
            "Speechiness",
            "Liveness",
            "Genre",
        ]
    )
    filtered_tracks_df = (
        filtered_tracks_df.drop(["Genre"], axis=1)
        .drop_duplicates()
        .reset_index(drop=True)
    )

    ### ------------------------------------------------------------------
    ### Output data and visual content to page
    if "song_selection" not in st.session_state:
        # if new session load, initialize with a random song from filtered list
        song_selection = np.random.randint(0, filtered_tracks_df.shape[0], 1)
    else:
        # otherwise, set song_selection to the same one set by widget
        song_selection = st.session_state.song_selection
    track = filtered_tracks_df.iloc[song_selection, :]

    # define tab containers for visualizations
    tab1, tab2, tab3 = st.tabs(
        ["Acoustic Print", "Comparative Radar (Song vs. Associated Genres)", "Bar"]
    )

    # define first tab as container for Acoustic Print
    with tab1:
        # if there is no song selection, empty container and show message
        if not song_selection:
            st.empty()
            st.write("Please select a song")
        else:
            # generate acoustic print
            DY_df = generate_fingerprint(track, category="dynamics")
            AR_df = generate_fingerprint(track, points=2000, category="articulation")

            # plot acoustic print
            plot_acoustic_print(track, DY_df, AR_df)

    # define second tab as container for Radar chart
    with tab2:
        # if there is no song selection, empty container and show message
        if not song_selection:
            st.empty()
            st.write("Please select a song")
        else:
            # get aggregated acoustic information based on the selected track's associate genres
            radar_df = get_filtered_acoustics(track, filtered_genres_df)

            # plot comparative acoustic radar
            plot_acoustic_radar(track, radar_df)

    # define third tab as container for Bar chart
    with tab3:
        # if there is no song selection, empty container and show message
        if not song_selection:
            st.empty()
            st.write("Please select a song")
        else:
            st.write(radar_df)

    # define song selection widget
    song_selection = st.multiselect(
        label="Song",
        options=list(range(0, filtered_tracks_df.shape[0])),
        default=song_selection,
        format_func=lambda x: f"{filtered_tracks_df.loc[x, 'Song']} by {filtered_tracks_df.loc[x, 'Artist']}",
        max_selections=1,
        key="song_selection",
    )

    # define table of tracks
    st.caption(body="Tracks", help="cmd+f/ctrl+f to search table")
    st.dataframe(
        filtered_tracks_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": None,
            "Valence": None,
            "Energy": None,
            "Danceability": None,
            "Acousticness": None,
            "Instrumentalness": None,
            "Speechiness": None,
            "Liveness": None,
            "Tempo": st.column_config.NumberColumn("Tempo (BPM)", format="%.2f"),
        },
    )


# main program
if __name__ == "__main__":
    main()
