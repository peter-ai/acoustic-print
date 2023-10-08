"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Album Page of the Acoustic Print web app
"""
# import external dependencies
import pandas as pd
import streamlit as st

# import user defined package
from acoustic_helpers import (
    get_audio_descriptions,
    get_sql_connect_str,
    plot_acoustic_bars,
    plot_acoustic_radar,
)


def main():
    # define local page config
    st.set_page_config(
        layout="wide", page_title="Acoustic Print - Album", page_icon="💿"
    )
    st.title("Album")

    try:
        ids = st.experimental_get_query_params()["id"]
        id = int(ids[0])
        if len(ids) > 1:
            st.caption("Only one album can be shown at a time.")

        conn_str = get_sql_connect_str()
        conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

        album_df = conn.query(
            f"""
            SELECT Ab.favorites AS Favorites, Ab.listens AS Listens, Ab.num_tracks AS `Number of Tracks`,
                Ab.release_date AS `Release Date`, Ab.title AS Title, Ar.name AS Artist, T.title AS `Track Name`,
                T.valence AS Valence, T.danceability AS Danceability, T.energy AS Energy, T.acousticness AS Acousticness, 
                T.instrumentalness AS Instrumentalness, T.speechiness AS Speechiness, T.liveness AS Liveness, 
                T.tempo AS Tempo, T.duration AS Duration
            FROM Albums Ab
                INNER JOIN Artists Ar
                    ON Ab.artist_id=Ar.id
                INNER JOIN Tracks T
                    ON Ab.id=T.album_id
            WHERE Ab.id={id} AND Ab.num_tracks<>0;
            """
        )
        st.dataframe(album_df)

        # if album has no tracks, raise exception
        if album_df.shape[0] == 0:
            raise ValueError

    except KeyError:
        st.write(
            "Oops, seems like the album you've selected is missing from the catalogue, please select another..."
        )
        st.stop()
    except ValueError:
        st.write(
            "Oops, seems like someone tinkered with the album identifier, it's invalid so please select another..."
        )
        st.stop()
    except Exception:
        st.write(
            "Oops, seems like the album you selected has no tracks on it, plase select another..."
        )
        st.stop()

    # provide recommendations
    with st.sidebar:
        st.write(
            f"""
            Similar Albums:
            * <a href="Album?id={1}">name</a>
            * <a href="Album?id={1}">name</a>
            * <a href="Album?id={1}">name</a>
            * <a href="Album?id={1}">name</a>
            * <a href="Album?id={1}">name</a>
            """,
            unsafe_allow_html=True,
        )

    # create audio feature description table
    feature_desc = get_audio_descriptions()
    st.divider()
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
