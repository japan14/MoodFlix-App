import streamlit as st
import random
import time
import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.cloud import bigquery
from google.cloud import exceptions
import json
import os



api_key = os.environ.get('API_KEY')
genai.configure(api_key=api_key)
model = GenerativeModel('gemini-pro')

client = bigquery.Client()

# create tuneflix dataset 
dataset_id = f'{client.project}.Tuneflix'
try:
    dataset = client.get_dataset(dataset_id)
except exceptions.NotFound:
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = 'US'
    dataset = client.create_dataset(dataset)

# create saved-playlist table
saved_playlist_table_id = f'{dataset_id}.saved-playlist'
try:
    saved_playlist_table = client.get_table(saved_playlist_table_id)
except exceptions.NotFound:
    schema = [
        bigquery.SchemaField("Name", "STRING"),
        bigquery.SchemaField("Songs", "JSON"),
        bigquery.SchemaField("time", "TIMESTAMP"),
    ]
    saved_playlist_table = bigquery.Table(saved_playlist_table_id, schema=schema)
    saved_playlist_table = client.create_table(saved_playlist_table)

# create favorites table
favorites_table_id = f'{dataset_id}.Favorites'
try:
    favorites_table = client.get_table(favorites_table_id)
except exceptions.NotFound:
    schema = [
        bigquery.SchemaField("Title", "STRING"),
        bigquery.SchemaField("Artist", "STRING"),
        bigquery.SchemaField("Genre", "STRING"),
        bigquery.SchemaField("Year", "INTEGER"),
    ]
    favorites_table = bigquery.Table(favorites_table_id, schema=schema)
    favorites_table = client.create_table(favorites_table)



col1, col2, col3 = st.columns([15, 16, 9])
col2.header("TUNEFLIX")
col1, col2, col3 = st.columns([15, 16, 9]) 
col2.markdown("<span style='color: #FFFFE0;'>Feel It. Hear It. TuneFlix</span>", unsafe_allow_html=True)


st.text("Welcome to TuneFlix! Tell us how you're feeling, we'll craft the perfect playlist")

col1, col2, col3 = st.columns([14, 16, 9])
col2.header("Your Playlists")
col1, col2, col3 = st.columns([15, 16, 9])
col2.markdown("<span style='color: #FFFFE0;'>Your Saved Playlists TuneFlix</span>", unsafe_allow_html=True)

# query to get saved playlist and songs from the saved-playlist table 
song_dict = {}
playlist_titles = []
query = f"SELECT name, songs FROM `{saved_playlist_table_id}` ORDER BY name"  
rows = client.query_and_wait(query)

# create a dictionary to map playlist names to the list of their songs
for row in rows:
    playlist_titles.append(row.name)
    song_dict[row.name] = row.songs 

# display the saved playlist names in a drop down select box, the songs are displayed when the search button is clicked
saved_title = st.selectbox("Select a Saved Playlist", playlist_titles)
search = st.button("Search")
st.session_state["search"] = []
if search and saved_title and saved_title in song_dict.keys():
    for value in song_dict[saved_title].split('''", '''):
        st.session_state["search"].append(value[1:])
        # col1, col2, col3 = st.columns([14, 16, 9])
        # col2.write(value[1:])

if st.session_state["search"]:
    for song in st.session_state["search"]:
        col1, col2, col3 = st.columns([14, 16, 9])
        col2.write(song)


col1, col2, col3 = st.columns([14, 16, 9])
col2.header("TuneFlix AI")


def type_writer_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.05)


col1, col2, col3 = st.columns([14, 16, 9])
col2.text("How are you feeling?")
description = st.text_input("I am feeling...")


prompt = (
            f"You are a music recommendation interface that recommends music that fits the user's mood"
            f"Create a {description} playlist."
            '''
            Provide a bulleted list with the following format:
                Create a name for the playlist:
                (input title of the song)\n
                Do not output the song title in quotation marks, and ONLY include the title of the song. 
                Do not include "Playlist: " in the playlist name, just print the name of the playlist. 
                Provide at least 8 songs, in each playlist.
            '''
    )

if "response" not in st.session_state:
    st.session_state["response"] = None
if "titles" not in st.session_state:
    st.session_state["titles"] = []
if "response_2" not in st.session_state:
    st.session_state["response_2"] = None
if "added_to_favorites" not in st.session_state:
    st.session_state["added_to_favorites"] = None
if "song_dict" not in st.session_state:
    st.session_state["song_dict"] = {}
if "saved" not in st.session_state:
    st.session_state["song_dict"] = None

if st.button("Generate"):
    response = model.generate_content(prompt)
    st.session_state["response"] = response.text  
    # st.write(response.text)
    
    st.session_state["titles"] = []
    for title in response.text.split('\n')[1:]:
        stripped_title = title.strip()
        if stripped_title:
            st.session_state["titles"].append(stripped_title[2:])
    # st.write(st.session_state["titles"])

if st.session_state["response"]:
    st.write(st.session_state["response"])
    response_lines = []
    for line in st.session_state["response"].split('\n'):
        response_lines.append(line)
    if response_lines: 
        playlist_name = response_lines[0]
    save = st.button("Save Playlist")

if st.session_state["response"] and save:
    titles_list = [title.strip('\n') for title in st.session_state['titles']]
    songs_json = json.dumps(titles_list)

    query = f"""
    INSERT INTO `{saved_playlist_table_id}` (Name, Songs) 
    VALUES (@name, @songs)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("name", "STRING", playlist_name),
            bigquery.ScalarQueryParameter("songs", "JSON", songs_json),
        ]
    )
    client.query_and_wait(query, job_config=job_config)
    
    st.session_state["saved"] = playlist_name
    st.write(f"{playlist_name} has been saved!")

# the user selects a song they want to know more about, ai api then generates more info about the song
if st.session_state["response"]:
    song = st.selectbox("Select a song to get more info", st.session_state["titles"])
    if song:
        next_prompt = (
            f'''
            Make it a bulleted list, with {song} as the main bullet, and sub-bullet artist, genre, and year 
                    Artist: (input artist / artists )\n
                    Genre: (input genre of the song)\n
                    Year: (input the year the song was released)\n
                    Do not output the song title in quotation marks. Only output information for ONE song, the song selected.
            '''
        )
        next_response = model.generate_content(next_prompt)
        st.session_state["response_2"] = next_response.text

if st.session_state["response_2"]:
        st.write(st.session_state["response_2"])
        fav_button = st.button("Add to favorites")

        lines = []
        for line in next_response.text.split('\n')[1:]:
            stripped_line = line.strip()
            if stripped_line:
                lines.append(stripped_line[2:])
        # st.write(lines)

        st.session_state["song_dict"] = {}
        for i in range(0, len(lines), 3):
            title = song
            artist = lines[i].split(": ")[1]
            genre = lines[i + 1].split(": ")[1]
            year = lines[i + 2].split(": ")[1]
            
            st.session_state["song_dict"][title] = [artist, genre, year]

if st.session_state["response_2"] and fav_button:
    if song and st.session_state["song_dict"].get(song):
        # query to check if the song is already in the favorites table, if not, add it
        query = f"Select Title FROM {favorites_table_id}"
        job_config = bigquery.QueryJobConfig(
            query_parameters = [
                bigquery.ScalarQueryParameter("song", "STRING", song)
            ]
        )
        rows = client.query_and_wait(query, job_config = job_config)

        if song in [row[0] for row in rows]:
            st.write(f"{song} already in Favorites!")
        # adding song to favorites
        else:
            query = f"INSERT INTO {favorites_table_id} (Title, Artist, Genre, Year) VALUES (@song, @artist, @genre, @year) "
            job_config = bigquery.QueryJobConfig(
                query_parameters = [
                    bigquery.ScalarQueryParameter("song", "STRING", song),
                    bigquery.ScalarQueryParameter("artist", "STRING", st.session_state["song_dict"][song][0]),
                    bigquery.ScalarQueryParameter("genre", "STRING", st.session_state["song_dict"][song][1]),
                    bigquery.ScalarQueryParameter("year", "INTEGER", int(st.session_state["song_dict"][song][2])),
                ]
            )
            client.query_and_wait(query, job_config = job_config)
            st.session_state["added_to_favorites"] = song
            st.write(f"Added '{song}' to favorites!")

