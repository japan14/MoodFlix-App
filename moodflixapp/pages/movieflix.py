import streamlit as st
import google.generativeai as genai
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
from PIL import Image
import io
from google.cloud import storage
from google.cloud import bigquery
import teamfunctions as tf

schema_dict =  { 'Date':'TIMESTAMP',
                'Search' : 'STRING',
                'Response' : 'STRING'}
table = tf.make_dataset('movieflix','recommendation',schema_dict)

# Title
st.title("MovieFlix 🎥")

# Slogan
st.header("The perfect movie, for every mood")

# Image
st.image("unplash_projector.jpg")

# About Section
st.subheader("Stuck in choosing what to watch?")
st.write("""Are you feeling lost in a sea of movie options? We get it. Selecting what to watch can be overwhelming. 
    That's where MovieFlix comes in. We're a revolutionary film recommendation app that pairs you 
    with a selection of movies catered to your mood! This is done by an AI-powered chatbot to provide you with the best recommendations."""
)

st.write("""You can also create an intro for your own movie based off of any photo!
    However, please note that this feature is still in development and may not have perfect results."""
    )


# Take user chat input and theme to generate responses
themes = ["Just Right for the Mood", 
    "Mind Bending", 
    "Underrated Hidden Gems", 
    "Musicals", 
    "Independent Films", 
    "Visually Stunning ", 
    "Classics",
    "Blockbusters"]


theme = st.selectbox("Select a category to guide your search", themes)
chat = st.text_input("How are you feeling? (Make sure you do not have any files selected before prompting!)")

# Generate response based on user input
if chat and theme:
    prompt = (
            "You are a movie recomendation interface that recomends films based on the user's mood.\n"
            f"Provide a list based on the FORMAT below of 5 movies that are {theme} and also match the mood of {chat}.\n\n"
            "FORMAT\n\n"
            "For example:\n\n"
            "***Title:*** The Shawshank Redemption (1994)\n\n"
            "***Synopsis:*** A banker is wrongly convicted of murdering his wife and sent to prison, where he must adapt to life behind bars and find a way to survive.\n\n"
            "***Why:*** This movie is a classic for a reason. It's a powerful and moving story about hope, redemption, and the human spirit.\n\n"
            "***Available on:*** Netflix, Amazon Prime Video\n\n"
        )
    chat = f"{theme},{chat.lower()}" 
    slicing = "***Title:*** "
    movies = tf.chat_prompt(chat, prompt, slicing, table)

    # Selecting a movie from the response
    st.subheader("What more would you like to know about the last recommendations?")
    categories = {"Cast" : f"Who is the cast of ", 
    "Reviews" : f"What are the reviews for ", 
    "Fun Fact" : f"What is a fun fact about ",
    "Image" : f"Generate an image based of this movie: "
    }
    tf.prompt_chaining(movies, categories)

# Take user image input and generates response
img = st.file_uploader("Make your own movie! 🎥", type=['png', 'jpg', 'jpeg'])
if img and not chat:
    prompt ="Based on the image, create an complete plot for a movie"
    tf.img_prompt(prompt, img)



    

    


        

