"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Home Page of the Acoustic Print web app
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
    get_sql_connect_str,
    plot_acoustic_print,
)


def main():
    # define local page config
    st.set_page_config(
        layout="wide",
        page_title="Acoustic Print - Home",
        page_icon="🏠",
        initial_sidebar_state="collapsed",
    )
    hide_pages(["Album"])
    show_artists = False

    # create database connection
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)
    st.write(conn.query("SELECT USER();"))
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

        ### Explore
        Explore the acoustic print of various songs and survey how the audio features of tracks compare to their broader genres
        on the <a href="Songs" target=_self style="text-decoration:none;">Songs</a> page. Click on an album in the table below 
        to see further details about it and how it compares relative to other music in the catalogue and interact with the
        visualizations shown throughout this web app.
        """,
        unsafe_allow_html=True,
    )

    feature_desc = get_audio_descriptions()
    with st.expander("See further details"):
        # TODO - Write stuff about data and analyss
        st.write(
            f"""
            ### Analysis
            Stuff about data and analysis ... [PLACEHOLDER] Polar Curves
            #### Description of Audio Features
            """
        )
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
        st.write(
            """
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
        """
    )

    # generate acoustic print polar curves
    DY_df = generate_acoustic_print(rand_song, category="dynamics")
    AR_df = generate_acoustic_print(rand_song, points=2000, category="articulation")

    # caption and plot acoustic print
    st.write("Acoustic Print")
    st.caption(
        f"{rand_song['Song'].iloc[0]} by {rand_song['Artist'].iloc[0]}",
    )
    plot_acoustic_print(DY_df, AR_df)

    # query database for albums data
    albums_df = conn.query(
        """ 
        SELECT Ab.id, Ab.title AS Album, Ab.release_date AS `Release Date`, Ab.num_tracks AS Songs,
            Ab.favorites AS Favorites, Ab.listens AS Listens, Ar.name AS Artist, Ab.artist_id
        FROM Albums Ab
            INNER JOIN Artists Ar
                ON Ab.artist_id=Ar.id
        WHERE Ab.num_tracks<>0 AND Ab.release_date IS NOT NULL;
        """
    )
    albums_df["Linkage"] = albums_df.apply(
        lambda row: [str(row["id"]), str(row["Album"])], axis=1
    )
    albums_df["Release Date"] = pd.to_datetime(
        albums_df["Release Date"], format="%Y-%M-%d"
    )

    # create caption for albums data
    st.caption(body="Albums", help="click an album to see details")

    # construct Aggrid builder and format the columns for the albums table
    builder1 = GridOptionsBuilder.from_dataframe(
        albums_df.filter(
            ["Linkage", "Artist", "Release Date", "Favorites", "Listens", "Songs"]
        )
    )
    builder1.configure_pagination(
        enabled=True, paginationAutoPageSize=False, paginationPageSize=50
    )
    builder1.configure_column(
        "Linkage",
        "Album",
        cellRenderer=JsCode(
            """
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    this.eGui.innerHTML = '<a href="/Album?id='+params.value[0]+'" target=_target style="text-decoration:none;">'+params.value[1]+'</a>';    
                }
                getGui() {
                    return this.eGui;
                }
            }
        """
        ),
    )
    builder1.configure_column(
        "Release Date",
        type=["customDateTimeFormat", "dateColumnFilter"],
        custom_format_string="yyyy-MM-dd",
    )
    builder1.configure_column("Favorites", headerClass="leftAligned")
    builder1.configure_column(
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
    builder1.configure_column("Songs", headerClass="leftAligned")

    # build and show albums table
    go1 = builder1.build()
    go1["autoSizeAllColumns"] = True
    AgGrid(
        albums_df.filter(
            ["Linkage", "Artist", "Release Date", "Favorites", "Listens", "Songs"]
        ),
        gridOptions=go1,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        allow_unsafe_jscode=True,
        enable_quicksearch=True,
    )

    # toggle showing artist table
    if show_artists:
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

        # join data to get most popular album
        artists_ag_df = pd.merge(
            left=artists_df,
            right=albums_df.loc[
                albums_df.groupby(by="Artist")["Favorites"].idxmax(),
                ["artist_id", "Album"],
            ],
            left_on="id",
            right_on="artist_id",
            how="inner",
        ).filter(["Artist", "Favorites", "Number of Albums", "Album"])

        # create caption for artists data
        st.caption(body="Artists")

        # construct Aggrid builder and format the columns for the artist table
        artist_grid = GridOptionsBuilder.from_dataframe(artists_ag_df)
        artist_grid.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=25,
        )
        artist_grid.configure_column("Album", "Most Popular Album")
        artist_grid.configure_column("Favorites", headerClass="leftAligned")
        artist_grid.configure_column("Number of Albums", headerClass="leftAligned")

        # build and show artist table
        go2 = artist_grid.build()
        AgGrid(
            artists_ag_df,
            fit_columns_on_grid_load=True,
            gridOptions=go2,
        )


# main program
if __name__ == "__main__":
    main()
