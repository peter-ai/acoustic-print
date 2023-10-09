"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Album Page of the Acoustic Print web app
"""
# import external dependencies
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_distances

# import user defined package
from acoustic_helpers import (
    get_audio_descriptions,
    get_filtered_acoustics,
    get_sql_connect_str,
    plot_acoustic_bars,
    plot_acoustic_radar,
    write_recs,
)


def main():
    # define local page config
    st.set_page_config(
        layout="wide", page_title="Acoustic Print - Album", page_icon="💿"
    )

    try:
        ids = st.experimental_get_query_params()["id"]
        id = int(ids[0])
        if len(ids) > 1:
            st.caption("Only one album can be shown at a time.")

        conn_str = get_sql_connect_str()
        conn = st.experimental_connection(name="acoustic_db", type="sql", url=conn_str)

        discography = conn.query(
            f"""
            SELECT Ab.favorites AS Favorites, Ab.listens AS Listens, T.favorites AS `Track Favorites`, T.listens as `Track Listens`,
                T.explicit AS Explicit, Ab.release_date AS `Release Date`, Ab.title AS Title, Ar.name AS Artist, 
                T.title AS Song, T.valence AS Valence, T.danceability AS Danceability, T.energy AS Energy, 
                T.acousticness AS Acousticness, T.instrumentalness AS Instrumentalness, T.speechiness AS Speechiness, 
                T.liveness AS Liveness, T.tempo AS Tempo, T.duration AS Duration, TG.genre_id, G.title AS Genre
            FROM Albums Ab
                INNER JOIN Artists Ar
                    ON Ab.artist_id=Ar.id
                INNER JOIN Tracks T
                    ON Ab.id=T.album_id
                INNER JOIN Track_Genres TG
                    ON TG.track_id=T.id
                INNER JOIN Genres G
                    ON TG.genre_id=G.id
            WHERE Ab.id={id};
            """
        )
        # if album has no tracks, raise exception
        if discography.shape[0] == 0 or discography["Release Date"].isna().iloc[0]:
            raise ValueError

        # display album info
        album_df = discography.filter(
            ["Title", "Release Date", "Artist", "Favorites", "Listens"]
        ).drop_duplicates()
        st.write(
            f"""
            # {album_df.Title.iloc[0]}
            #### Artist: {album_df.Artist.iloc[0]} (released {album_df["Release Date"].iloc[0].strftime("%b %d, %Y")})
            ##### {album_df.Favorites.iloc[0]} {'favorite' if album_df.Favorites.iloc[0] == 1 else 'favorites'} & {album_df.Listens.iloc[0]:,} {'listen' if album_df.Listens.iloc[0] == 1 else 'listens'}
            """
        )

        # process data to plot on radar chart and bar chart
        album_stats_df = discography.filter(
            [
                "Valence",
                "Danceability",
                "Energy",
                "Acousticness",
                "Instrumentalness",
                "Speechiness",
                "Liveness",
            ]
        ).mean(axis=0)

        genres_ids = tuple(discography.genre_id.unique())
        genres = tuple(discography.Genre.unique())
        albums_by_genre = conn.query(
            f"""
            SELECT Ab.id AS id, Ab.title AS Title, G.title AS Genre, Ar.name AS Artist, AVG(T.valence) AS Valence, 
                AVG(T.danceability) AS Danceability, AVG(T.energy) AS Energy, AVG(T.acousticness) AS Acousticness, 
                AVG(T.instrumentalness) AS Instrumentalness, AVG(T.speechiness) AS Speechiness, 
                AVG(T.liveness) AS Liveness, AVG(T.tempo) AS Tempo, SUM(T.duration) AS Duration
            FROM Albums Ab
                INNER JOIN Tracks T
                    ON Ab.id=T.album_id
                INNER JOIN Artists Ar
                    ON Ab.artist_id=Ar.id
                INNER JOIN Track_Genres TG
                    ON TG.track_id=T.id
                INNER JOIN Genres G
                    ON TG.genre_id=G.id
            WHERE Ab.num_tracks<>0 AND G.id IN ({" ,".join((str(id) for id in genres_ids))}) 
                AND Ab.id<>{id} AND Ab.release_date IS NOT NULL
            GROUP BY Ab.id, Ab.title, G.title, TG.genre_id;
            """,
        )
        genre_stats_df = (
            albums_by_genre.drop(["id", "Title", "Tempo", "Duration", "Artist"], axis=1)
            .groupby("Genre", as_index=False)
            .mean()
        )
        genre_stats_df["id"] = "1"

        tab1, tab2 = st.tabs(["Comparative Radar", "Comparative Bar"])
        with tab1:
            radar_df = get_filtered_acoustics(
                album_stats_df, genre_stats_df, genres=genres, songs=False
            )

            st.write("Audio Features of Current Album vs. Albums in Associated Genres")
            st.caption(
                "",
                help="click on legend items to change visibility; double-click to isolate",
            )

            plot_acoustic_radar(radar_df)

        with tab2:
            bar_df = radar_df.copy(deep=True)
            bar_df.columns = [
                "Audio Features",
                "Music Subset",
                "Values",
            ]

            # plot acoustic bars
            st.write("Audio Features of Current Album vs. Albums in Associated Genres")
            st.caption(
                "",
                help="click on legend items to change visibility; double-click to isolate",
            )
            plot_acoustic_bars(bar_df)

        # recommendation system
        with st.sidebar:
            recommendations = {}
            for i, genre in enumerate(genres):
                if i == 0:
                    st.write(
                        f"""<ul style="margin-bottom:0px;">Similar {genre} Albums:</ul>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.write(
                        f"""<ul style="margin-top:1rem; margin-bottom:0px;">Similar {genre} Albums:</ul>""",
                        unsafe_allow_html=True,
                    )
                # filter for necessary data
                recs_stats_df = albums_by_genre.loc[
                    albums_by_genre.Genre == genre, :
                ].drop(["Genre", "Tempo", "Duration"], axis=1)
                recs_details_df = recs_stats_df.filter(
                    ["id", "Title", "Artist"]
                ).set_index("id")
                recs_stats_df = recs_stats_df.drop(["id", "Title", "Artist"], axis=1)

                # compute cosine distance
                cos_dis = cosine_distances(
                    recs_stats_df, album_stats_df.to_numpy().reshape(1, -1)
                ).reshape(
                    -1,
                )

                # get albums with minimum cosine distances
                genre_recs = recs_details_df.iloc[
                    np.argpartition(cos_dis, 11)[:3], :
                ].reset_index(drop=False)

                # write recommendation list
                genre_recs.apply(write_recs, axis=1, recommendations=recommendations)

        # display info about tracks on album
        tracks_df = (
            discography.filter(
                ["Song", "Duration", "Track Favorites", "Track Listens", "Explicit"]
            )
            .rename(
                {"Track Favorites": "Favorites", "Track Listens": "Listens"}, axis=1
            )
            .drop_duplicates()
        )
        tracks_df["Duration"] = tracks_df.Duration.apply(
            lambda x: f"{x//60}:{x-((x//60)*60):02d}"
        )
        tracks_df["Explicit"] = tracks_df.Explicit.apply(
            lambda x: "Ambiguous" if x == -1 else "No" if x == 0 else "Yes"
        )
        st.write("Track List")
        st.dataframe(tracks_df, use_container_width=True, hide_index=True)

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

    except KeyError as e:
        st.write(
            "Oops, seems like the album you've selected is missing from the catalogue, please select another..."
        )
        st.stop()
    except ValueError:
        st.write(
            "Oops, seems like someone tinkered with the album identifier, it's invalid so please select another..."
        )
        st.stop()
    except Exception as e:
        st.write(e)
        st.write(
            "Oops, seems like the album you selected has no tracks on it, plase select another..."
        )
        st.stop()


# main program
if __name__ == "__main__":
    main()
