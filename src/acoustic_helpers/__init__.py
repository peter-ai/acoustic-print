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
    energy_desc = "Measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy."
    dance_desc = "Describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable."
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
def get_tracks(_conn, sql_query):
    """
    get_tracks queries database and gets all tracks from the database

    Parameters
    ----------
    _conn : sqlalchemy
        a connection to a MySQL database
    sql_query : _type_
        query string for MySQL database

    Returns
    -------
    pd.DataFrame
        a pandas dataframe of all tracks in the database
    """
    return _conn.query(sql_query)


@st.cache_data
def get_filtered_tracks(
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
):
    """
    get_filtered_tracks gets filtered tracks based on user selected parameters

    Parameters
    ----------
    tracks_df : pd.DataFrame
        a pandas dataframe of tracks
    min_valence : float
        minimum valence selected by user
    max_valence : float
        maximum valence selected by user
    min_energy : float
        minimum energy selected by user
    max_energy : float
        maximum energy selected by user
    min_dance : float
        minimum danceability selected by user
    max_dance : float
        maximum danceability selected by user
    min_acoustics : float
        minimum acousticness selected by user
    max_acoustics : float
        maximum acousticness selected by user
    min_instrument : float
        minimum instrumentalness selected by user
    max_instrument : float
        maximum instrumentalness selected by user
    min_speech : float
        minimum speechiness selected by user
    max_speech : float
        maximum speechiness selected by user
    min_live : float
        minimum liveness selected by user
    max_live : float
        maximum liveness selected by user
    min_tempo : float
        minimum tempo selected by user
    max_tempo : float
        maximum tempo selected by user
    min_duration : float
        minimum duration selected by user
    max_duration : float
        maximum duration selected by user
    explicit_vals : list
        filter on explicit music

    Returns
    -------
    _type_
        _description_
    """
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

    return (filtered_tracks_df, filtered_genres_df)


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
def generate_acousticprint(data, points=3000, category="dynamics"):
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


def plot_acoustic_print(dynamics_df, articulation_df):
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

    # define the first trace (subplot); Rhythm & Dynamics
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

    # define the second trace (subplot); Articulation & Texture
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

    # update positioning, legend details, coloring, and margins
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

    # make plot transparent with no axes visible
    fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)

    # generate caption and plot
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def get_filtered_acoustics(data, filtered_genres_df):
    """
    get_filtered_acoustics _summary_

    Parameters
    ----------
    data : pd.DataFrame
        1xN pandas dataframe containing the audio features for a song
    filtered_genres_df : pd.DataFrame
        a pandas dataframe of songs filtered based on user-provided parameters

    Returns
    -------
    pd.DataFrame
        a pandas dataframe containing aggregated acoustic features for a song and its
        associated genres
    """
    # get genres associated with selected track
    genre = filtered_genres_df.loc[filtered_genres_df.id == data.id.iloc[0], "Genre"]

    # reformat audio information about given track
    track_radar = data.filter(
        [
            "Valence",
            "Energy",
            "Danceability",
            "Acousticness",
            "Instrumentalness",
            "Speechiness",
            "Liveness",
        ],
    ).T.reset_index(drop=False)
    track_radar["Genre"] = "Current Song"
    track_radar.columns = ["index", "value", "Genre"]
    track_radar = track_radar[
        [
            "index",
            "Genre",
            "value",
        ]
    ]

    # filter songs based on relevant genres and aggregate audio features per genre
    genre_radar = (
        filtered_genres_df.loc[
            filtered_genres_df.Genre.isin(genre),
            :,
        ]
        .drop("id", axis=1)
        .groupby(by="Genre", as_index=True)
        .mean()
    ).T.reset_index(drop=False)
    genre_radar = pd.melt(
        genre_radar, id_vars=["index"], value_vars=genre_radar.columns[1:]
    )

    # combine computed audio features with those from song and reformat dataframe
    radar_df = pd.concat([track_radar, genre_radar], ignore_index=True)
    radar_df.columns = ["Theta", "Song's Genres", "Rho"]

    # return final dataframe
    return radar_df


def plot_acoustic_radar(radar_df):
    """
    plot_acoustic_radar plots the radar/spider chart of the current song selection
    and the average across its associated genres

    Parameters
    ----------
    data : pd.DataFrame
        1xN pandas dataframe containing the audio features for a song
    radar_df : pd.DataFrame
        a pandas dataframe containing aggregated acoustic features for a song and its
        associated genres
    """
    # plot radar chart
    fig = px.line_polar(
        data_frame=radar_df,
        r="Rho",
        theta="Theta",
        line_close=True,
        markers=True,
        color="Song's Genres",
        line_shape="spline",
    )

    # update coloring, plot margins, and legend positioning
    fig.update_traces(fill="toself", textposition="top center")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(
            yanchor="middle",
            y=0.65,
            x=0.8,
        ),
    )

    # make plot background transparent
    fig.update_polars(bgcolor="rgba(0,0,0,0)")

    # generate caption and plot
    st.plotly_chart(fig, use_container_width=True)


def plot_acoustic_bars(bar_df):
    """
    plot_acoustic_bars plots the bar chart of the current song selection
    and the average across its associated genres and subsets of the music catalogue

    Parameters
    ----------
    bar_df : pd.DataFrame
        a pandas dataframe containing rlevant information for plotting bars
    """
    # create bar chart
    fig = px.bar(
        data_frame=bar_df,
        x="Audio Features",
        y="Values",
        color="Track Subset",
        barmode="group",
    )

    # update opacity
    fig.update_traces(opacity=0.75)

    # generate plot
    st.plotly_chart(fig, use_container_width=True)
