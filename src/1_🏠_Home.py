"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA)
to create visual acoustic fingerprints of songs and compare audio characteristics 
across the music catalogue. The app is built on Streamlit.

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
    st.experimental_set_query_params()
    st.set_page_config(
        layout="wide",
        page_title="Acoustic Print - Home",
        page_icon="🏠",
        initial_sidebar_state="collapsed",
    )
    hide_pages(["Album"])
    show_artists = False

    ### ------------------------------------
    ### Headers, background, project context
    st.title("Acoustic-Print")
    st.write(
        """
        **Author: Peter Akioyamen** (see [@peter-ai](https://github.com/peter-ai/acoustic-print) for the full github repo)
        
        ### Context
        Traditionally, an acoustic fingerprint is a digital summary that is generated from an audio signal deterministically. 
        It provides a method to identify an audio signal quickly, and allows for the lookup of similar audio signals 
        based on the fingerprint. 
        
        **Acoustic-Print** is a project that seeks to develop a visual representation of an acoustic fingerprint with a similar 
        foundation in mind; 1) the acoustic print of a song should be deterministic and 2) songs that share similar 
        audio characteristics should have similar acoustic prints. A dual visualization is created that represents a new
        *Acoustic Print*, deviating a bit from the traditional definition. One visualization represents Rhythm & Dynamics 
        (comprised of valence, energy, and danceability) while the the other represents Articulation & Texture 
        (comprised of speechiness, instrumentalness, and acousticness), both embedding information about the 
        tempo of the song (see further details below).

        Explore the acoustic print of various songs and survey how the audio features of tracks compare to one another
        on the <a href="Songs" target=_self style="text-decoration:none;">Songs</a> page. Click on an album in the table below 
        to view its audio characteristics, and get recommendations of similar albums across genres. All visualizations are live,
        so have fun.
        """,
        unsafe_allow_html=True,
    )

    ### -----------------------------
    ### Descrpition of audio features
    feature_desc = get_audio_descriptions()
    with st.expander("See further details"):
        st.write(
            f"""
            #### Important Notes
            Data on which this project is built is from the Free Musich Archive (FMA), in particular,
            from the study *FMA: A Dataset For Music Analysis* by Michaël Defferrard, Kirell Benzi, 
            Pierre Vandergheynst, and Xavier Bresson. Unfortunately, given the nature of the archive, 
            you will likely not see many songs from the most popular performers and your favorite artists.
            Due to rate limiting on the Spotify API and a policy against the use of Spotify data for machine
            learning, using recent data for this project was less feasible. Nonetheless, I hope you enjoy.

            #### Analysis
            Each visualization representing the acoustic print of a song is produced through a combination of
            polar curves that have been fixed at the origin in a given cartesian plane. The shape of each
            curve considers a song's tempo and one other distinct audio feature. As a result, each polar 
            curve in a given acoustic print encodes a unique characteristic of the song it is representing.

            Since the feature space is fairly small and the features also have the same range, album recommendations 
            are genereated via euclidean distances. Clustering as a precursor to identifying similar albums was explored. 
            The existence of meaningful and/or separable clusters was low so there was little justification to use a more 
            complicated recommendation pipeline, given results from traditional distance/similarity metrics were highly comparable.
            
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
    st.divider()

    ### -----------------------------------------------
    ### Retrieve data and visualize random track choice
    # connect to database
    conn_str = get_sql_connect_str()
    conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

    # query database for random track from db
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
        f"**Spontaneous song selection:** {rand_song['Song'].iloc[0]} by {rand_song['Artist'].iloc[0]}",
    )
    plot_acoustic_print(DY_df, AR_df)

    ### ---------------------------
    ### Display albums in catalogue
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

    # construct Aggrid builder and format the columns for the albums table
    builder1 = GridOptionsBuilder.from_dataframe(
        albums_df.filter(
            ["Linkage", "Artist", "Release Date", "Favorites", "Listens", "Songs"]
        )
    )
    builder1.configure_pagination(  # configure pagination
        enabled=True, paginationAutoPageSize=False, paginationPageSize=50
    )
    builder1.configure_column(  # configure a hyperlinked album column
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
    builder1.configure_column(  # reformat release date column
        "Release Date",
        type=["customDateTimeFormat", "dateColumnFilter"],
        custom_format_string="yyyy-MM-dd",
    )
    builder1.configure_column(
        "Favorites", headerClass="leftAligned"
    )  # left align Favorites column header
    builder1.configure_column(  # left align Listnes column header and comma delimit values
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
    builder1.configure_column(
        "Songs", "Number of Songs", headerClass="leftAligned"
    )  # left align Favorites column header

    # build albums table, create caption and show  table
    go1 = builder1.build()
    go1["autoSizeAllColumns"] = True
    st.caption(body="Albums", help="click an album to see details")
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
