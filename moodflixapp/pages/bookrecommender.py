import streamlit as st
import google.generativeai as genai
from PIL import Image
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
from google.cloud import bigquery
import teamfunctions as tf
#from google.cloud.exceptions import NotFound
import os


#ai config and model, also bigquery
api_key = os.environ.get('API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')
client = bigquery.Client()

#imagen set up
vertexai.init(project=client.project, location="us-central1")
imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@005")

def main():
    st.title("Moodflix")

    col1, col2 = st.columns(2)
    with col1:
        st.header("Book Recommender")
    with col2:
        st.header("Ultimate Guide to Book Suggestions")

    st.image("unsplah-book.jpg", use_column_width=True)
    
    st.write("How are you feeling today😊😔?")

    mood_input = st.text_input("Enter mood below (e.g happy, sad, curious):")
    

    #getting custom created dataset
    schema = {
            "Title": "STRING",
            "Author": "STRING",
            "Description": "STRING"
        }
    table = tf.make_dataset("books_data","book_information",schema)
    
    #doing query from Bigquery
    query = (f'SELECT title from {table}')
    query_job = client.query(query)
    book_table = query_job.result()

    formatted_query = ""
    #formatted as a string
    for row in book_table:
        row_str = row['title']
        formatted_query += row_str + "\n"
    print(formatted_query)

    response = None
    if mood_input:
        if mood_input in st.session_state:
            books = st.session_state[mood_input]
        else:
            st.title("Book Suggestions")
            #AI call and prompt
            prompt = (f"From the list {formatted_query} suggest five books for someone that is feeling {mood_input}.Return the response in a comma separated format with title,author, summary and genre as columns.")

            try:
                response = model.generate_content(prompt)
                st.write(response.text)
            except ValueError:
                st.write("Model is unable to process this request. Try again!")

    
            #storing book suggestiond for follow up
            #used gemini to find how to parse book suggestions
            books = []
            for book in response.text.splitlines():
                title = book.split(',')[0]
                books.append(title)
            st.session_state[mood_input] = books
 

        #prompt chaining
        st.write("Which of these books would you like to know about?")
        book_options = {"generate" : f"Generate a quote from ", 
        "suggestion" : f"Based on {mood_input} why is this suggested ", "Image" : f"Generate the cover of "}
        tf.prompt_chaining(books, book_options)#chain calling based on selected book

        #download books
        if response:
            download = st.download_button(label="Download Content", data=response.text,file_name="book_suggestions.txt")
            if download:
                st.info("Downloaded successfully!")


    
if __name__ == '__main__':
    main()
