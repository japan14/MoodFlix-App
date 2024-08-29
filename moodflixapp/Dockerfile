FROM python:3.9-slim
WORKDIR /moodflixapp
COPY . .
RUN pip3 install -r requirements.txt
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "main.py", "--server.enableCORS=false", "--server.port=8501", "--server.address=0.0.0.0"]
