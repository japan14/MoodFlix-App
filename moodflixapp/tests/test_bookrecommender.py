from streamlit.testing.v1 import AppTest
from unittest.mock import patch

at = AppTest.from_file("../pages/bookrecommender.py").run()

@patch("bookrecommender.genai.GenerativeModel")
def test_user_text(mockGenerativeModel):
    
    assert not at.exception

    mockModel = mockGenerativeModel.return_value
    mockResponse = mockModel.generate_content.return_value
    mockResponse.text = [
        {"title": "Book1", "author": "Author1", "summary": "Summary1", "genre": "Genre1"},
        {"title": "Book2", "author": "Author2", "summary": "Summary2", "genre": "Genre2"},
        {"title": "Book3", "author": "Author3", "summary": "Summary3", "genre": "Genre3"},
        {"title": "Book4", "author": "Author4", "summary": "Summary4", "genre": "Genre4"},
        {"title": "Book5", "author": "Author5", "summary": "Summary5", "genre": "Genre5"}
    ]

    at.text_input[0].set_value("happy").run()

    assert at.title[1].body == "Book Suggestions"
    assert at.markdown[0].body == (
        "Title,Author,Summary,Genre\n"
        "Book1,Author1,Summary1,Genre1\n"
        "Book2,Author2,Summary2,Genre2\n"
        "Book3,Author3,Summary3,Genre3\n"
        "Book4,Author4,Summary4,Genre4\n"
        "Book5,Author5,Summary5,Genre5"
    )
    mockModel.generate_content.assert_called_once_with(
        "suggest five books for someone that is feeling happy.Format the response in a csv format with title,author, summary and genre as columns.")

def test_generate_button():
    at = AppTest.from_file("bookrecommender.py").run()
    at.button[0].click()

    assert at.button[0].label == "generate"
    assert at.button[0].click == True
