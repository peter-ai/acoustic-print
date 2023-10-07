CREATE DATABASE Acoustics;
USE Acoustics;

CREATE TABLE Artists (
    id int PRIMARY KEY,
    favorites int,
    name varchar(60)
);

CREATE TABLE Albums (
    id int PRIMARY KEY,
    artist_id int NOT NULL,
    favorites int,
    listens int,
    num_tracks int,
    release_date date,
    title varchar(100),
    FOREIGN KEY (artist_id) REFERENCES Artists (id)
);

CREATE TABLE Tracks (
    id int PRIMARY KEY, 
    artist_id int NOT NULL,
    album_id int,
    acousticness float,
    danceability float,
    energy float,
    instrumentalness float,
    liveness float,
    speechiness float,
    tempo float,
    valence float,
    FOREIGN KEY (album_id) REFERENCES Albums (id),
    FOREIGN KEY (artist_id) REFERENCES Artists (id),
    duration int,
    explicit int,
    favorites int,
    listens int,
    title varchar(150)
);

CREATE TABLE Genres (
    id int PRIMARY KEY,
    num_tracks int,
    title varchar(55),
    genre_color varchar(7)
);

CREATE TABLE Track_Genres (
    track_id int NOT NULL,
    genre_id int NOT NULL,
    FOREIGN KEY (track_id) REFERENCES Tracks (id),
    FOREIGN KEY (genre_id) REFERENCES Genres (id)
);

SHOW TABLES;