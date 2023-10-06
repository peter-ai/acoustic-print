"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Home Page of the Acoustic Print web app
"""
# import packages from standard libraries
import os

# import external dependencies
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots

# define global variables
MAX_TEMPO = 251.072
MIN_TEMPO = 12.75


@st.cache_data
def get_sql_connect_str():
    """
    get_sql_connect_str generates a database connection string from environment variables

    Returns
    -------
    str
        connection string for MySQL databas
    """
    # load variables from .env file into set of environment variables
    load_dotenv()

    # get environment variables for database connection
    hostname = os.getenv("HOSTNAME")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    database = os.getenv("DATABASE")
    port = 3306

    # create db connection str and MySQL engine pool
    conn_str = f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}"

    return conn_str


@st.cache_data
def pol2cart(rho, theta):
    """
    pol2cart transforms a set of polar coordinates to cartesian coordinates

    Parameters
    ----------
    rho : int, float, np.array
        a numerical type that represents rho in polar coordinates
    theta : int, float, np.array
        a numerical type that represents theta in polar coordinates

    Returns
    -------
    2xN tuple
        a tuple containing x and y coordinates
    """
    x = rho * np.cos(theta)
    y = rho * np.sin(theta)
    return (x, y)


@st.cache_data
def norm_tempo(tempo):
    """
    norm_tempo normalizes tempo values of tracks to fall in (0, 10]

    Parameters
    ----------
    tempo : float
        a floating point number representing the tempo of a song in range

    Returns
    -------
    float
        a floating point number representing the normalizaed tempo value

    Raises
    ------
    ValueError
        raised when tempo outside acceptable range of (12.75, 251.072]
    """
    if tempo <= MIN_TEMPO or MAX_TEMPO < tempo:
        raise ValueError
    return ((tempo - MIN_TEMPO) / (MAX_TEMPO - MIN_TEMPO)) * 10


@st.cache_data
def generate_fingerprint(data, points=1500, category="dynamics"):
    """
    generate_fingerprint produces the acoustic fingerprint for a given song
    base on its measured audio features

    Parameters
    ----------
    data : pd.DataFrame
        1xN pandas dataframe containing the audio features for a song
    points : int, optional
        number of points that should be plotted for a given curve, by default 1500
    category : str, optional
        the set of curves we are computing, by default "dynamics"

    Returns
    -------
    pd.DataFrame
        pointsx4 dataframe containing columns necessary to generate acoustic print of a song

    Raises
    ------
    TypeError
        raised when there is a mismatch in arguments provided and expected types
    ValueError
        raised when argument for category does not fall within expected values
    """
    # ensure appropriate data types are provided
    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"Expected pd.DataFrame but received data of type {type(data)}."
        )
    if not isinstance(points, int):
        raise TypeError(
            f"Expected pd.DataFrame but received data of type {type(data)}."
        )
    if not isinstance(category, str):
        raise TypeError(
            f"Expected pd.DataFrame but received data of type {type(data)}."
        )

    # define number of points to evaluate and where to evaluate them in polar coords
    theta = np.linspace(0, 48 * np.pi, points)
    plane = np.zeros(points)

    if category == "dynamics":
        # define song parameters
        tempo = data["Tempo"].to_numpy()
        valence = data["Valence"].to_numpy()
        energy = data["Energy"].to_numpy()
        danceability = data["Danceability"].to_numpy()

        # compute rho in polar coords for each song parameter under Rhythm & Dynamics grouping
        valence_rho = tempo * np.cos(5 * theta * valence) + 1
        energy_rho = tempo * np.cos(5 * theta * energy) + 1
        danceability_rho = tempo * np.cos(5 * theta * danceability) + 1

        # convert (rho, theta) in polar coords to (x, y) in cartesian
        x_valence, y_valence = pol2cart(valence_rho, theta)
        x_energy, y_energy = pol2cart(energy_rho, theta)
        x_danceability, y_danceability = pol2cart(danceability_rho, theta)

        # create dataframe for Rhythm & Dynamics
        acoustic_print = pd.DataFrame(
            {
                "Attribute": np.repeat(["Valence", "Energy", "Danceability"], points),
                "X": np.concatenate((x_valence, plane, y_danceability)),
                "Y": np.concatenate((y_valence, x_energy, plane)),
                "Z": np.concatenate((plane, y_energy, x_danceability)),
            }
        )
    elif category == "articulation":
        # define song parameters
        tempo = data["Tempo"].to_numpy()
        acousticness = data["Acousticness"].to_numpy()
        instrumentalness = data["Instrumentalness"].to_numpy()
        speechiness = data["Speechiness"].to_numpy()

        # compute rho in polar coords for each song parameter under Articulation & Texture grouping
        acoustic_rho = norm_tempo(tempo) * (
            np.sin(2 * theta * speechiness) + np.cos(3 * theta * acousticness)
        )
        instrumental_rho = norm_tempo(tempo) * (
            np.sin(2 * theta * speechiness) + np.cos(3 * theta * instrumentalness)
        )
        speech_rho = norm_tempo(tempo) * (
            np.sin(2 * theta * speechiness) + np.cos(3 * theta * speechiness)
        )

        # convert (rho, theta) in polar coords to (x, y) in cartesian
        x_acoustic, y_acoustic = pol2cart(acoustic_rho, theta)
        x_instrumental, y_instrumental = pol2cart(instrumental_rho, theta)
        x_speech, y_speech = pol2cart(speech_rho, theta)

        # define dataframes for Articulation & Texture
        acoustic_print = pd.DataFrame(
            {
                "Attribute": (["Acousticness"] * points)
                + (["Instrumentalness"] * points)
                + (["Speechinees"] * points),
                "X": np.concatenate((x_acoustic, plane, y_speech)),
                "Y": np.concatenate((y_acoustic, x_instrumental, plane)),
                "Z": np.concatenate((plane, y_instrumental, x_speech)),
            }
        )
    else:
        raise ValueError(
            f"Valid values for category are 'dynamics' or 'articulation', not {category}."
        )

    # return requested acoustic print
    return acoustic_print


def plot_acoustic_print(data, dynamics_df, articulation_df):
    """
    TODO: Docstring


    plot_acoustic_print _summary_

    Parameters
    ----------
    data : _type_
        _description_
    dynamics_df : _type_
        _description_
    articulation_df : _type_
        _description_
    """

    # create figure object with subplots
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "scatter3d"}, {"type": "scatter3d"}]],
        horizontal_spacing=0.01,
        subplot_titles=["Rhythm & Dynamics", "Articulation & Texture"],
    )

    # define the first trace (subplot)
    t1 = px.line_3d(
        data_frame=dynamics_df,
        x="X",
        y="Y",
        z="Z",
        color="Attribute",
        width=1600,
        height=800,
    )
    t1.update_traces(
        legendgroup=1, legendgrouptitle=dict(text="Rhythm & Dynamics"), legend="legend"
    )
    fig.add_traces(t1.data, rows=1, cols=1)

    # define the second trace (subplot)
    t2 = px.line_3d(
        data_frame=articulation_df,
        x="X",
        y="Y",
        z="Z",
        color="Attribute",
        width=1600,
        height=800,
    )
    t2.update_traces(
        legendgroup=2,
        legendgrouptitle=dict(text="Articulation & Texture"),
        legend="legend2",
    )
    fig.add_traces(t2.data, rows=1, cols=2)

    fig.update_layout(
        scene=dict(
            bgcolor="rgba(0,0,0,0)",
        ),
        scene_aspectmode="cube",
        margin=dict(l=20, r=20, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.1,
            xanchor="center",
            x=0.5,
            tracegroupgap=10,
        ),
    )
    fig.layout.annotations[0].update(y=0.85)
    fig.layout.annotations[1].update(y=0.85)

    fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)

    st.caption(f"Current Acoustic Print: {data['Name'][0]} by {data['Artist'][0]}")
    st.plotly_chart(fig, use_container_width=True)


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
        **Author: Peter Akioyamen** ([see @peter-ai](https://github.com/peter-ai/acoustic-print) for the full github repo)
        
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
