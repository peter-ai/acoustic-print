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
    generate_acousticprint,
    get_audio_descriptions,
    get_filtered_acoustics,
    get_filtered_tracks,
    get_sql_connect_str,
    get_tracks,
    plot_acoustic_bars,
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

    ### ---------------------------------------
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

    ### -----------------------------
    ### Database connection and query
    # connect to database
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

    # query database for all tracks
    sql_query = """
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
    tracks_df = get_tracks(conn, sql_query)

    # filter table of tracks based on user provided parameters
    filtered_tracks_df, filtered_genres_df = get_filtered_tracks(
        tracks_df,
        min_valence,
        max_valence,
        min_energy,
        max_energy,
        min_dance,
        max_dance,
        min_acoustics,
        max_acoustics,
        min_instrument,
        max_instrument,
        min_speech,
        max_speech,
        min_live,
        max_live,
        min_tempo,
        max_tempo,
        min_duration,
        max_duration,
        explicit_vals,
    )

    ### --------------------------------------
    ### Output data and visual content to page
    # define song selection widget
    filtered_ids = filtered_tracks_df.id
    if "song_selection" not in st.session_state:
        # if song selection is not in session state, it has not occurred so set default values
        song_selection = st.selectbox(
            label="Song",
            options=filtered_tracks_df.id,
            format_func=lambda x: " by ".join(
                filtered_tracks_df.iloc[
                    np.where(filtered_ids == x)[0], :2
                ].values.tolist()[0]
            ),
            key="song_selection",
        )
    else:
        try:
            # otherwise it has occurred so attempt to set previous selection to the current selection
            song_selection = st.selectbox(
                label="Song",
                options=filtered_ids,
                index=filtered_ids.index[
                    list(filtered_ids).index(st.session_state["song_selection"])
                ],
                format_func=lambda x: f"{filtered_tracks_df.iloc[np.where(filtered_ids==x)[0], 0].iloc[0]} by {filtered_tracks_df.iloc[np.where(filtered_ids==x)[0], 1].iloc[0]}",
                key="song_selection",
            )
        except ValueError as e:
            # previous selection is no longer in the filtered results so reset selection to default
            song_selection = st.selectbox(
                label="Song",
                options=filtered_ids,
                format_func=lambda x: f"{filtered_tracks_df.iloc[np.where(filtered_ids==x)[0], 0].iloc[0]} by {filtered_tracks_df.iloc[np.where(filtered_ids==x)[0], 1].iloc[0]}",
                key="song_selection",
            )
        finally:
            if song_selection == None:
                # if selection is None, e.g., there are no values within filter params, stop app and send message
                st.write("Please broaden filters to see results...")
                st.stop()

    track = filtered_tracks_df.loc[filtered_tracks_df.id == song_selection, :]

    # define tab containers for visualizations
    tab1, tab2, tab3 = st.tabs(
        ["Acoustic Print", "Comparative Radar", "Comparative Bar"]
    )

    # define first tab as container for Acoustic Print
    with tab1:
        # if there is no song selection, empty container and show message
        if song_selection == None:
            st.empty()
            st.write("Please select a song")
        else:
            # generate acoustic print
            DY_df = generate_acousticprint(track, category="dynamics")
            AR_df = generate_acousticprint(track, category="articulation")

            # plot acoustic print
            st.caption(f"{tracks_df['Song'].iloc[0]} by {tracks_df['Artist'].iloc[0]}")
            plot_acoustic_print(DY_df, AR_df)

    # define second tab as container for Radar chart
    with tab2:
        # if there is no song selection, empty container and show message
        if song_selection == None:
            st.empty()
            st.write("Please select a song")
        else:
            # get aggregated acoustic information based on the selected track's associate genres
            radar_df = get_filtered_acoustics(track, filtered_genres_df)

            # plot comparative acoustic radar
            st.write("Audio Features of Current Song vs. Associated Genres")
            st.caption(
                f"{tracks_df['Song'].iloc[0]} by {tracks_df['Artist'].iloc[0]}",
                help="click on legend items to change visibility; double-click to isolate",
            )
            plot_acoustic_radar(radar_df)

    # define third tab as container for Bar chart
    with tab3:
        # if there is no song selection, empty container and show message
        if song_selection == None:
            st.empty()
            st.write("Please select a song")
        else:
            # reformat filtered bars and aggregate data
            bar_df = (
                filtered_tracks_df.drop(
                    [
                        "Song",
                        "Artist",
                        "Album",
                        "Duration",
                        "Favorites",
                        "Listens",
                        "Tempo",
                        "id",
                    ],
                    axis=1,
                )
                .mean(axis=0)
                .reset_index(drop=False)
            )
            bar_df["Song's Genres"] = "Catalogue (filtered)"
            bar_df.columns = ["Theta", "Rho", "Song's Genres"]
            bar_df = pd.concat([bar_df, radar_df], ignore_index=True)

            # aggregate data across all tracks in music catalogue
            catalogue_df = (
                tracks_df.drop(
                    [
                        "Song",
                        "Artist",
                        "Album",
                        "Duration",
                        "Favorites",
                        "Listens",
                        "Genre",
                        "Tempo",
                        "Explicit",
                    ],
                    axis=1,
                )
                .drop_duplicates()
                .drop(["id"], axis=1)
                .mean(axis=0)
                .reset_index(drop=False)
            )
            catalogue_df["Track Subset"] = "Catalogue (total)"

            # rename and union datasets
            catalogue_df.columns = bar_df.columns = [
                "Audio Features",
                "Values",
                "Track Subset",
            ]
            bar_df = pd.concat([bar_df, catalogue_df], ignore_index=True).sort_values(
                by="Track Subset"
            )

            # plot acoustic bars
            st.write(
                "Audio Features of Current Song vs. Associated Genres and Music Catalogue Subsets"
            )
            st.caption(
                f"{tracks_df['Song'].iloc[0]} by {tracks_df['Artist'].iloc[0]}",
                help="click on legend items to change visibility; double-click to isolate",
            )
            plot_acoustic_bars(bar_df)

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
