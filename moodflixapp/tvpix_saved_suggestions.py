from google.cloud import bigquery
import streamlit as st
import os
import io

# Function to insert suggestions into BigQuery table
client = bigquery.Client()

def suggestions_to_bigquery(user, suggestion1, suggestion2, suggestion3, description):
    # Connect to BigQuery client
    
    PROJECT_ID = client.project
    LOCATION = "us-central1"
    dataset_name = "tvpix"
    table_name = "suggestions"

    table = f"{PROJECT_ID}.{dataset_name}.{table_name}"
    
    try:
        # Insert the suggestions into BigQuery table
        query = f'''
        INSERT INTO {table} (user, suggestion1, suggestion2, suggestion3, description)
        VALUES (@user, @suggestion1, @suggestion2, @suggestion3, @description)
        '''
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user", "STRING", user),
                bigquery.ScalarQueryParameter("suggestion1", "STRING", suggestion1),
                bigquery.ScalarQueryParameter("suggestion2", "STRING", suggestion2),
                bigquery.ScalarQueryParameter("suggestion3", "STRING", suggestion3),
                bigquery.ScalarQueryParameter("description", "STRING", description)
            ]
        )

        # Execute the query
        job = client.query(query, job_config=job_config)

        # Wait for the job to complete
        rows = job.result()
    
    except Exception as e:
            print(e)

def user_suggestions(user):
    try:
        PROJECT_ID = client.project
        LOCATION = "us-central1"
        dataset_name = "tvpix"
        table_name = "suggestions"

        table = f"{PROJECT_ID}.{dataset_name}.{table_name}"

        if user:
            # Query to retrieve saved suggestions
            query = f'''
            SELECT description, suggestion1, suggestion2, suggestion3
            FROM {table}
            WHERE user = @user
            '''
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("user", "STRING", user)]
            )
            query_job = client.query(query, job_config=job_config)
            query_result = query_job.result()

            # Display saved suggestions as a bulleted list
            for row in query_result:
                # Extract suggestion values from the row
                description = row["description"]
                suggestion1 = row["suggestion1"]
                suggestion2 = row["suggestion2"]
                suggestion3 = row["suggestion3"]

                suggestions_list = [suggestion1, suggestion2, suggestion3]
                suggestions_string = "\n".join([f" - {s}" for s in suggestions_list])
                st.write(f"When you were in a {description} mood:")
                st.write(suggestions_string)
    except Exception as e:
        st.error(f"An error has occurred: {e}")

def user_has_saved(user):
    try:

        PROJECT_ID = client.project
        LOCATION = "us-central1"
        dataset_name = "tvpix"
        table_name = "suggestions"

        table = f"{PROJECT_ID}.{dataset_name}.{table_name}"
        
        query = f'''
        SELECT COUNT(*) as count
        FROM {table}
        WHERE user = @user
        '''
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("user", "STRING", user)]
        )
        query_job = client.query(query, job_config=job_config)
        query_result = query_job.result()

        # Check if the user has saved any suggestions
        for row in query_result:
            count = row["count"]
            if count > 0:
                print("User has saved suggestions:", user)
                return True
            else:
                print("User has no saved suggestions:", user)
                return False
    
    except Exception as e:
        print(e)
        return False