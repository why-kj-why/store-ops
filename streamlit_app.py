import streamlit as st
import requests
import pandas as pd
import pymysql

DB_HOST = "tellmoredb.cd24ogmcy170.us-east-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "2yYKKH8lUzaBvc92JUxW"
DB_PORT = "3306"
DB_NAME = "retail_panopticon"
CONVO_DB_NAME = "store_questions"

if 'history' not in st.session_state:
    st.session_state['history'] = []


def connect_to_db(db_name):
    return pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASS,
        db=db_name
    )


def send_message_to_api(message):
    api_url = "http://127.0.0.1:5000/response"
    payload = {
        "database": DB_NAME,
        "query": message
    }
    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Error decoding JSON")
            return None
    else:
        print(f"Error: HTTP {response.status_code} - {response.text}")
        return None


def execute_query(query, connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            getResult = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
        return pd.DataFrame(getResult, columns=columns)
    finally:
        connection.close()


def store_question_in_db(question, sql_query):
    connection = connect_to_db(CONVO_DB_NAME)
    query = "INSERT INTO pinned_questions (question, sql_query) VALUES (%s, %s)"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (question, sql_query))
        connection.commit()
    finally:
        connection.close()


st.title("Store Ops")

for chat in st.session_state.history:
    st.write(f"**User:** {chat['question']}")
    st.write(f"**Natural Language Response:** {chat['nlr']}")
    # st.write(f"**SQL Query:** {chat['sql']}")

user_input = st.text_input("You: ")

if st.button("STORE"):
    if st.session_state.history:
        last_chat = st.session_state.history[-1]
        store_question_in_db(last_chat['question'], last_chat['sql'])
        st.success("Last conversation stored.")
    else:
        st.warning("No conversation to store.")

if user_input:
    api_response = send_message_to_api(user_input)
    if api_response and 'Engine Response' in api_response:
        st.session_state.history.append({
            "question": user_input,
            "nlr": api_response.get('Engine Response', 'No response provided'),
            "sql": api_response.get('Query SQL', 'No SQL provided')
        })
        conn = connect_to_db(DB_NAME)
        result = execute_query(api_response['Query SQL'], conn)
        st.dataframe(result, height=200)
        st.write(f"**Natural Language Response:** {api_response['Engine Response']}")
        st.write(f"**SQL Query:** {api_response['Query SQL']}")
    else:
        st.error("Failed to get a valid response from the API")
