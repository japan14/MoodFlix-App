import streamlit as st
from io import BytesIO

def download_suggestions(saved_suggestions, filename="TVPix_suggestions.txt"):
    suggestions_text = "\n".join(saved_suggestions)
    suggestions_bytes = suggestions_text.encode()
    suggestions_file = BytesIO(suggestions_bytes)
    st.download_button(
        label="**Download Suggestions**",
        data=suggestions_file,
        file_name=filename,
        mime="text/plain",
    )
    # Set the session state variable to True indicating the download button has been clicked
    st.session_state.download_button_clicked = True
    

    # Check if the download button has been clicked
    if st.session_state.download_button_clicked:
        st.info("Your suggestions have been downloaded! Please check your downloads folder.")
        
        st.session_state.download_button_clicked = False
