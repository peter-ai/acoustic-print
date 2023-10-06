# import packages from standard libraries
import os

# import external dependencies
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots


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
def get_audio_descriptions():
    """
    get_audio_descriptions defines strig descriptions of the audio features available for the songs

    Returns
    -------
    list
        descriptions of each audio feature
    """
    valence_desc = "A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry)."
    dance_desc = "Describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable."
    energy_desc = "Measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy."
    acoustic_desc = "A confidence measure from 0.0 to 1.0 of whether the track is acoustic. 1.0 represents high confidence the track is acoustic."
    instrumental_desc = "Predicts whether a track contains no vocals. 'Ooh' and 'aah' sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly 'vocal'. The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content. Values above 0.5 are intended to represent instrumental tracks, but confidence is higher as the value approaches 1.0."
    speech_desc = "Detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks."
    tempo_desc = "The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration."
    live_desc = "Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live. A value above 0.8 provides strong likelihood that the track is live."

    return [
        valence_desc,
        dance_desc,
        energy_desc,
        acoustic_desc,
        instrumental_desc,
        speech_desc,
        tempo_desc,
        live_desc,
    ]


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

    # define global variables
    max_tempo = 251.072
    min_tempo = 12.75

    # check that tempo is within valid range
    if tempo <= min_tempo or max_tempo < tempo:
        raise ValueError
    else:
        return ((tempo - min_tempo) / (max_tempo - min_tempo)) * 10


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
    plot_acoustic_print plots the acoustic-print comprised of polar curves that uniquely identifies
    the given song and displays the resulting figure in full-page width.


    Parameters
    ----------
    data : pd.DataFrame
        1xN pandas dataframe containing the audio features for a song
    dynamics_df : pd.DataFrame
        Mx4 dataframe containing columns necessary to generate Rhythm & Dynamics acoustic print of a song
    articulation_df : pd.DataFrame
        Mx4 dataframe containing columns necessary to generate Articulation & Texture acoustic print of a song
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

    st.caption(f"Acoustic Print: {data['Name'][0]} by {data['Artist'][0]}")
    st.plotly_chart(fig, use_container_width=True)


def plot_acoustic_radar():
    # TODO: Write function
    pass


def plot_acoustic_bars():
    # TODO: Write function
    pass
