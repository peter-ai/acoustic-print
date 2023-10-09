"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA)
to create visual acoustic fingerprints of songs and compare audio characteristics 
across the music catalogue. The app is built on Streamlit.

Songs Page of the Acoustic Print web app
"""
# import external dependencies
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_pages import hide_pages

# import user defined package
from acoustic_helpers import (
    generate_acoustic_print,
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
    st.experimental_set_query_params()
    st.set_page_config(
        layout="wide",
        page_title="Acoustic Print - Songs",
        page_icon="🎵",
        initial_sidebar_state="collapsed",
    )
    hide_pages(["Album"])
    st.title("Songs")

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
            format_func=lambda x: "Ambiguous" if x == -1 else "No" if x == 0 else "Yes",
        )

    ### -----------------------------
    ### Database connection and query
    # connect to database
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

    # query database for all tracks
    sql_query = """
        SELECT T.title AS `Song`, AR.name AS Artist, AB.title AS Album, AB.release_date, AB.num_tracks, 
            T.duration AS Duration, T.Favorites AS Favorites, T.listens AS Listens, G.title AS Genre,
            T.valence AS Valence, T.energy AS Energy, T.danceability AS Danceability,
            T.acousticness AS Acousticness, T.instrumentalness AS Instrumentalness, T.speechiness AS Speechiness,
            T.liveness AS Liveness, T.tempo AS Tempo, T.id, T.album_id, T.explicit AS Explicit
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
    filtered_ids = filtered_tracks_df[["id", "Song", "Artist"]].set_index("id")
    filtered_ids["Name"] = filtered_ids.Song.str.cat(filtered_ids.Artist, sep=" by ")
    if "song_selection" not in st.session_state:
        # if song selection is not in session state, it has not occurred so set default values
        song_selection = st.selectbox(
            label="Song selection",
            options=filtered_ids.index.values,
            format_func=lambda x: filtered_ids.loc[x, "Name"],
            key="song_selection",
        )
    else:
        song_selection = st.session_state.song_selection
        try:
            # otherwise it has occurred so attempt to set previous selection to the current selection
            song_selection = st.selectbox(
                label="Song selection",
                options=filtered_ids.index.values,
                index=filtered_ids.index.to_list().index(
                    st.session_state["song_selection"]
                ),
                format_func=lambda x: filtered_ids.loc[x, "Name"],
                key="song_selection",
            )
        except ValueError as e:
            # previous selection is no longer in the filtered results so reset selection to default
            song_selection = st.selectbox(
                label="Song selection",
                options=filtered_ids.index.values,
                format_func=lambda x: filtered_ids.loc[x, "Name"],
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
            DY_df = generate_acoustic_print(track, category="dynamics")
            AR_df = generate_acoustic_print(track, category="articulation")

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
            st.write("Audio Features of Current Song vs. Songs in Associated Genres")
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
                        "release_date",
                        "album_id",
                        "num_tracks",
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
            catalogue_df["Music Subset"] = "Catalogue (total)"

            # rename and union datasets
            catalogue_df.columns = bar_df.columns = [
                "Audio Features",
                "Values",
                "Music Subset",
            ]
            bar_df = pd.concat([bar_df, catalogue_df], ignore_index=True).sort_values(
                by="Music Subset"
            )

            # plot acoustic bars
            st.write(
                "Audio Features of Current Song vs. Songs in Associated Genres and Music Catalogue Subsets"
            )
            st.caption(
                f"{tracks_df['Song'].iloc[0]} by {tracks_df['Artist'].iloc[0]}",
                help="click on legend items to change visibility; double-click to isolate",
            )
            plot_acoustic_bars(bar_df)

    # define table of tracks
    st.caption(body="Tracks", help="cmd+f/ctrl+f to search table, open panel to filter")

    # construct Aggrid builder and format the columns for the tracks table
    builder1 = GridOptionsBuilder.from_dataframe(
        filtered_tracks_df.drop(
            [
                "id",
                "Valence",
                "Energy",
                "Danceability",
                "Acousticness",
                "Instrumentalness",
                "Speechiness",
                "Liveness",
            ],
            axis=1,
        )
    )
    builder1.configure_default_column(
        filterable=False
    )  # make columns unfilterable given streamlit filters above
    builder1.configure_pagination(  # configure pagination
        enabled=True, paginationAutoPageSize=False, paginationPageSize=50
    )
    builder1.configure_column(  # configure a hyperlinked album column
        "Album",
        cellRenderer=JsCode(
            """
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    this.eGui.innerHTML = params.value[0] == 'false' ? params.value[1] : '<a href="/Album?id='+params.value[0]+'" target=_target style="text-decoration:none;">'+params.value[1]+'</a>';    
                }
                getGui() {
                    return this.eGui;
                }
            }
        """
        ),
    )
    builder1.configure_column(  # comma format favorites column
        "Favorites",
        headerClass="leftAligned",
        cellRenderer=JsCode(
            """
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    this.eGui.innerHTML = Number(params.value).toLocaleString("en-US");
                }
                getGui() {
                    return this.eGui;
                }
            }
            """
        ),
    )
    builder1.configure_column(  # comma format listens column
        "Listens",
        headerClass="leftAligned",
        cellRenderer=JsCode(
            """
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    this.eGui.innerHTML = Number(params.value).toLocaleString("en-US");
                }
                getGui() {
                    return this.eGui;
                }
            }
            """
        ),
    )
    builder1.configure_column(  # format tempo to two decimals
        "Tempo",
        headerClass="leftAligned",
        cellRenderer=JsCode(
            """
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    this.eGui.innerHTML = Number(params.value).toFixed(2);
                }
                getGui() {
                    return this.eGui;
                }
            }
            """
        ),
    )

    # build and show Aggrid table
    go1 = builder1.build()
    go1["autoSizeAllColumns"] = True
    AgGrid(
        filtered_tracks_df.drop(
            [
                "id",
                "Valence",
                "Energy",
                "Danceability",
                "Acousticness",
                "Instrumentalness",
                "Speechiness",
                "Liveness",
            ],
            axis=1,
        ),
        gridOptions=go1,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        allow_unsafe_jscode=True,
        enable_quicksearch=True,
    )

    # create audio feature description table
    st.divider()
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


# main program
if __name__ == "__main__":
    main()
