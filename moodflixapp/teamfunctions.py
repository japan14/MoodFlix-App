import streamlit as st
import google.generativeai as genai
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
from PIL import Image
from google.cloud import storage
from google.cloud.exceptions import NotFound
from datetime import datetime
from google.cloud import bigquery
import io
import os

# GenAI Model Set Up
api_key = os.environ.get('API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')
vision = genai.GenerativeModel('gemini-pro-vision')

#BigQuery client set up
client = bigquery.Client()

# Image Gen Set Up
PROJECT_ID = client.project
LOCATION = "us-central1"
vertexai.init(project = PROJECT_ID, location = LOCATION)
img_gen = ImageGenerationModel.from_pretrained("imagegeneration@005")


"""
******WORKS ONLY FOR MOVIEFLIX******
Input:
    chat = Text input from user
    prompt = What will the Gen AI do with user input (make your own, depending in how you want to set the Gen AI to output its responses)
    slicing_parm = What is before each recomendation (i.e, bullet, dash, category names, etc) from the response
Output:
    A GUI that displays the recomendations stored in the backend, if theres no previous recommendations then the response comes from the Gen AI, 
    and returns a list of string of recomendations generated by the model.
Note:
    1. The slicing_parm should be based in how you set the Gen AI to output its responses.
    2. The result is used in chain_prompt() as the response_lst parameter
Example:
    chat = "Happy"
    prompt = (
         "You are a movie recomendation interface that recomends films based on the user's mood.\n"
        f"Provide a list based on the FORMAT below for a list of 5 movies based on the mood of {chat}.\n\n"
        "FORMAT\n\n"
        "For example:\n\n"
        "***Title:*** The Shawshank Redemption (1994)\n\n"
        "***Synopsis:*** A banker is wrongly convicted of murdering his wife and sent to prison, where he must adapt to life behind bars and find a way to survive.\n\n"
        "***Why:*** This movie is a classic for a reason. It's a powerful and moving story about hope, redemption, and the human spirit.\n\n"
        "***Available on:*** Netflix, Amazon Prime Video\n\n"
    )
    slicing_parm = ***Tittle***
    #Aftermaking Gen AI calls
        result = [The Shawhank Redemption (1994)\n\n", Recomendation 1, Recomendation 2, Recomendation 3, Recomendation 4, Recomendation 5]]
"""
def chat_prompt(chat, prompt, slicing_parm, table):
    QUERY = (f"SELECT Response FROM {table} WHERE Search = @chat")
    job_config = bigquery.QueryJobConfig(
        query_parameters = [
            bigquery.ScalarQueryParameter("chat", "STRING",chat)
        ]
    )
    query_job = client.query(QUERY, job_config= job_config) 
    rows = query_job.result()
    result = []

    if rows.total_rows > 0:
        for row in rows:
            suggestion = row.Response

    else:
        st.write("Querying Gen AI because this is a new search!")
        response = model.generate_content(prompt)
        suggestion = response.text

        myquery = f"""INSERT INTO {table} (Date, Search, Response)  
                VALUES (CURRENT_TIMESTAMP(), @chat, @response)"""
        job_config = bigquery.QueryJobConfig(
            query_parameters = [
                bigquery.ScalarQueryParameter("chat", "STRING",chat),
                bigquery.ScalarQueryParameter("response", "STRING",response.text)
            ]
        )
        
        QUERY = (myquery)
        query_job = client.query(QUERY, job_config=job_config)
        rows = query_job.result()

    for line in suggestion.split('\n'):
        if line.startswith(slicing_parm):
            result.append(line[len(slicing_parm):])
            st.subheader(line)
        else:
            st.write(line)
    st.download_button("Download", data=suggestion, file_name="MovieFlix_recommendations.txt")

    return result

"""
Input: 
    response_lst: list of recomendations generated by the model
    categories_dic: dictionary of categories and prompts (make your own, depending on what type of chaining you want to achive)
        Key = Button/Category
        Value = Prompt
Output: 
    A GUI that displays the recomendations in a selectbox and buttons for each category that will be chain prompted.
    
Note: 
    1. The Gen AI will recieve the prompt as follows: prompt + options
    2. This function can also generate images with with a Key = "Image"
Example: 
    response_lst = ["Up", "Option 2", "Option 3"]
    categories_dic = {
    "Cast" : f"Who is the cast of ", 
    "Reviews" : f"What are the reviews for ", 
    "Fun Fact" : f"What is a fun fact about ", 
    "Image" : f"Generate an image based of this movie: "
    }
    #User wants to see the cast of up
        >Prompt = categories_dic["Cast"] + options = f"Who is the cast of Up?"
"""
def prompt_chaining(response_lst, categories_dic):
    if response_lst and categories_dic:
        options = st.selectbox("Select a recomendation", response_lst)
        for category, prompt in categories_dic.items():
            button = st.button(category)
            if button:
                if category == "Image":
                    response = img_gen.generate_images(prompt= prompt + options)
                    if len(response.images) > 0:
                        image = Image.open(io.BytesIO(response.images[0]._image_bytes))
                        if image:
                            st.image(image)
                    else:
                        st.write("Error, please try again")
                else:
                    try:
                        response = model.generate_content(prompt + options)
                        st.write(response.text)
                    except ValueError:
                        st.write("Model is unable to process this request. Try again!")
    else:
        st.write("No recomendations found")

"""
Input:
    img = Image input from user
    prompt = What will the Gen AI do with user input (make your own, depending in how you want to set the Gen AI to output its responses)
Output:
    A GUI that displays the user input and the response from the Gen AI.
"""
def img_prompt(prompt, img):
    image = Image.open(img)
    st.image(img)
    response = vision.generate_content([prompt, image])
    response.resolve()
    st.write(response.text)

"""
Input:
    STRING dataset_name = name of dataset to verify or create 
    STRING table_name = name of table to verify or create
    schema_dict = dictionary of rows and types that will be the basis for the table
        KEY = Row name Ex: 'Response'
        VALUE = Row type Ex: 'STRING'
Output:
    Creates a dataset based of the client if it does not exists.
    Also a table based of the schema given if it does not exists.
"""
def make_dataset(dataset_name, table_name, schema_dict):
    dataset_id = f'{client.project}.{dataset_name}'
    try:
        dataset = client.get_dataset(dataset_id)
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = 'US'
        dataset = client.create_dataset(dataset)

    table_id = f'{dataset_id}.{table_name}'
    try:
        table = client.get_table(table_id)
    except NotFound:
        schema = []
        for attribute, data_type in schema_dict.items():
            schema.append(bigquery.SchemaField(attribute,data_type))
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
    return table

"""
Input:
    STRING table_name = name of table to verify or create
    schema_dictionary = dictionary of rows and types that will be the basis for the table
        KEY = Row name
        VALUE = Row type
Output:
    Creates a table based of the schema given if it does not exists.
"""



  