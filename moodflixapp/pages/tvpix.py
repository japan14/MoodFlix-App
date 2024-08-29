import google.generativeai as genai
import streamlit as st
# import vertexai
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tvpix_saved_suggestions
from tvpix_saved_suggestions import suggestions_to_bigquery, user_suggestions, user_has_saved
from io import BytesIO
import teamfunctions as tf

# GenAI Model Setup
api_key = os.environ.get('API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# PROJECT_ID = client.project
# LOCATION = "us-central1"
# vertexai.init(project=PROJECT_ID, location=LOCATION)

schema_dict = {'description': 'STRING', 'suggestion1': 'STRING', 'suggestion2': 'STRING', 'suggestion3': 'STRING', 'user': 'STRING'}
table = tf.make_dataset('tvpix', 'suggestions', schema_dict)

def get_username():
    user = st.text_input("**Welcome User:**")
    submit_button = st.button("Submit")
    print("User input in get_username:", user)
    if submit_button and user:
        print("User in get_username before return:", user) 
        st.success(f"Welcome {user}!")
        return user
    elif submit_button and not user:
        st.warning("Please enter a username.")
        #return None
    return user

def main():
    # Title, tagline, and heading
    st.title("***TV Pix*** 📺")
    st.header("***TV Tailored to Your Mood, We’ll Show You How You Feel!***")
    st.subheader("***Welcome to TV Pix!***")

    user = get_username()
    print("User in main:", user)
    if user:
        st.subheader("**What are you in the mood to watch?**")
        description = st.text_input("Tell us how you're feeling, and we'll find the perfect TV show to match your mood!")
        has_saved = user_has_saved(user)

        if has_saved:
            st.subheader("**Here's your saved suggestions:**")
            user_suggestions(user)


        if description:
            if description in st.session_state:
                tv_shows = st.session_state[description]
            else:
                prompt = (
                    f"List some TV shows that a user would watch if they were feeling {description}. "
                    "Answer as list of just 3 shows and the title of the TV shows."
                    "Include the year the show first aired in parenthesis next to the show title."
                    "Be inclusive of all show genres and the representation on the shows."
                    "Include both popular and unpopular shows."
                )
                response = model.generate_content(prompt)

                print(response.text)

                # Generated TV shows get stored here
                tv_shows = []
                for show in response.text.splitlines():
                    tv_shows.append(show[2:])
                st.session_state[description] = tv_shows

                selected_shows = tv_shows[:3]

                if "saved_suggestions_to_bigquery" not in st.session_state:
                    st.session_state.saved_suggestions_to_bigquery = []

                st.session_state.saved_suggestions_to_bigquery.append((user, selected_shows, tv_shows[0], tv_shows[1], tv_shows[2], description))
                
                if "saved_suggestions_displayed" not in st.session_state:
                    user_suggestions(user)
                    st.session_state.saved_suggestions_displayed = True
                # Save the suggestions to session state
                if "saved_suggestions" not in st.session_state:
                    st.session_state.saved_suggestions = []
                st.session_state.saved_suggestions.extend(selected_shows)


            # Header displays after user gives their mood
            st.subheader("***That's how you FEEL? We've got just the thing:***")

            # Creating columns for each of the 3 suggestions to go into
            col1, col2, col3 = st.columns(3)

            # Each show being saved to a variable to be displayed as the header of the column    
            show1 = col1.subheader(tv_shows[0])
            show2 = col2.subheader(tv_shows[1])
            show3 = col3.subheader(tv_shows[2])

            with col1:
                genre1 = st.button(f"How would you classify this show?", key="genre1")
                what1 = st.button(f"Why did you suggest this show for someone feeling {description}?", key="what1")
                star1 = st.button("Who stars in this show?", key="star1")
                about1 = st.button("What is this show about?", key="about1")
                length1 = st.button(f"How long are the episodes?", key="length1")
            with col2:
                genre2 = st.button(f"How would you classify this show?", key="genre2")
                what2 = st.button(f"Why did you suggest this show for someone feeling {description}?", key="what2")
                star2 = st.button("Who stars in this show?", key="stas2")
                about2 = st.button("What is this show about?", key="about2")
                length2 = st.button(f"How long are the episodes?", key="length2")
            with col3:
                genre3 = st.button(f"How would you classify this show?", key="genre3")
                what3 = st.button(f"Why did you suggest this show for someone feeling {description}?", key="what3")
                star3 = st.button("Who stars in this show?", key="star3")
                about3 = st.button("What is this show about?", key="about3")
                length3 = st.button(f"How long are the episodes?", key="length3")

                # Streamlit does not allow duplicate button inputs, each button in a column needs a unique key
                genres = [genre1, genre2, genre3]
                whats = [what1, what2, what3]
                stars = [star1, star2, star3]
                abouts = [about1, about2, about3]
                lengths = [length1, length2, length3]

                selected_shows = tv_shows[:3]

            # Looping through each button function for each show in a column
            # I used Gemini to get the lines that check if each button has been clicked to make sure that when a button is clicked, the output is only related to the column its in
            for i, show in enumerate(selected_shows):
                # Checking that the 'genre' button is clicked
                # commit this change in Github -- simplified the conditonal to loop through each button in each column
                if genres[i]:
                    prompt = f"What genre is the genre of {show}?"
                    response = model.generate_content(prompt)
                    st.write(response.text)

                # Checking that the 'what' button is clicked
                if whats[i]:
                    prompt = f"Why would you suggest this {show} to someone in a {description} mood?"
                    response = model.generate_content(prompt)
                    st.write(response.text)

                # Checking that the 'star' button is clicked
                if st.session_state.get(f"star{i+1}"):
                    if stars[i]:
                        prompt = f"Who are some notable actors and actresses in this {show}? What other shows may I recognize them from?"
                        response = model.generate_content(prompt)
                        st.write(response.text)
                # Checking that the 'about' button is clicked        
                if abouts[i]:
                    prompt = f"What is the plot summary of {show}?"
                    response = model.generate_content(prompt)
                    st.write(response.text)

                # Checking that the 'length' button is clicked
                if lengths[i]:
                    prompt = f"How long are the episodes of {show}?"
                    response = model.generate_content(prompt)
                    st.write(response.text)

            # Users can find where suggested shows are streaming
            st.subheader("***FEELING these suggestions? You can watch these shows here:***")
            for i, show in enumerate(selected_shows):
                streaming = st.button(f"Where is {show} streaming currently?", key=f"streaming{i+1}")

                if st.session_state.get(f"streaming{i+1}"):
                    prompt = f"Where can I watch this {show}?"
                    response = model.generate_content(prompt)
                    st.write(response.text)

            # Users can display and download their previous TV show suggestions
            st.subheader("We'll remember what you were in the mood to watch!")
            # if "saved_suggestions" not in st.session_state:
            #     st.session_state.saved_suggestions = []

            if "saved_suggestions_to_bigquery" not in st.session_state:
                st.session_state.saved_suggestions_to_bigquery = []

            if st.button("**Save Suggestions**"):
                st.info("Your suggestions are being saved!")
                # Call the function to save suggestions to BigQuery
                suggestions_to_bigquery(user, tv_shows[0], tv_shows[1], tv_shows[2], description)
                st.success("Your suggestions have been successfully saved!")

                if not user_has_saved(user):
                    st.session_state.saved_suggestions_to_bigquery.append((user, selected_shows, tv_shows[0], tv_shows[1], tv_shows[2], description))

                if "saved_suggestions_displayed" not in st.session_state:
                    user_suggestions(user)
                    st.session_state.saved_suggestions_displayed = True
                # Save the suggestions to session state
                if "saved_suggestions" not in st.session_state:
                    st.session_state.saved_suggestions = selected_shows

                # Download suggestions
                suggestions_text = "\n".join(st.session_state.saved_suggestions)
                suggestions_bytes = suggestions_text.encode()
                suggestions_bytes_io = BytesIO(suggestions_bytes)
                if st.download_button(label="**View** and **Download Suggestions**", data=suggestions_bytes_io, file_name="TVPix_suggestions.txt", mime="text/plain"):
                    st.success("Your suggestions have been successfully downloaded!")

main()
            

