import streamlit as st
import requests
import pandas as pd
import pymysql
import time

DB_HOST = "tellmoredb.cd24ogmcy170.us-east-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "2yYKKH8lUzaBvc92JUxW"
DB_PORT = "3306"
# DB_NAME = "retail_panopticon"
DB_NAME = "claires_data"
CONVO_DB_NAME = "store_questions"

CLAIRE_DEEP_PURPLE = '#553D94'

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'display_df_and_nlr' not in st.session_state:
    st.session_state['display_df_and_nlr'] = False

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""


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

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def set_custom_css():
    custom_css = """
    <style>
    
        .st-emotion-cache-9aoz2h.e1vs0wn30 {
            display: flex;
            justify-content: center; /* Center-align the DataFrame */
        }
        .st-emotion-cache-9aoz2h.e1vs0wn30 table {
            margin: 0 auto; /* Center-align the table itself */
        }
        
    </style>
    """
    # Inject the CSS
    st.markdown(custom_css, unsafe_allow_html=True)

set_custom_css()

#Load the logo 

with open(r'Claires_logo.svg', 'r') as image:
    image_data = image.read()
    
    
st.logo(image=image_data)

# Claire Purple top bar on Top.
st.markdown("""
<div style="position: fixed; top: 0; left: 0; width: 100%; height: 100px; background-color: {}; z-index: 1000;">
</div>
""".format(CLAIRE_DEEP_PURPLE), unsafe_allow_html=True)

st.markdown("""
    <h4 style="background-color: {}; color: white; padding: 10px;">
        Store Ops App
    </h4>
""".format(CLAIRE_DEEP_PURPLE), unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# st.title("Store Ops")

for chat in st.session_state.history:
    st.write(f"**User:** {chat['question']}")
    st.write(f"**Natural Language Response:** {chat['nlr']}")
    # st.write(f"**SQL Query:** {chat['sql']}")

# user_input = st.text_input("You: ")
st.session_state['user_input'] = st.text_input("You: ", st.session_state['user_input'])

# if st.button("STORE"):
#     if st.session_state.history:
#         last_chat = st.session_state.history[-1]
#         store_question_in_db(last_chat['question'], last_chat['sql'])
#         st.success("Last conversation stored.")
#     else:
#         st.warning("No conversation to store.")

if st.button("STORE"):
    if st.session_state.history:
        last_chat = st.session_state.history[-1]
        store_question_in_db(last_chat['question'], last_chat['sql'])
        st.success("Last conversation stored.")
        # Clear the chatbox
        st.session_state['user_input'] = ""
        # Hide the DataFrame and NLR
        st.session_state['display_df_and_nlr'] = False
        st.session_state['last_result'] = None
        st.session_state['last_nlr'] = None
    else:
        st.warning("No conversation to store.")

if st.session_state['user_input']:
    # api_response = send_message_to_api(user_input)
    # if api_response and 'Engine Response' in api_response:
    #     st.session_state.history.append({
    #         "question": user_input,
    #         "nlr": api_response.get('Engine Response', 'No response provided'),
    #         "sql": api_response.get('Query SQL', 'No SQL provided')
    #     })
    #     conn = connect_to_db(DB_NAME)
    #     result = execute_query(api_response['Query SQL'], conn)
    #     st.dataframe(result, height=200)
    #     st.write(f"**Natural Language Response:** {api_response['Engine Response']}")
    #     st.write(f"**SQL Query:** {api_response['Query SQL']}")
    # else:
    #     st.error("Failed to get a valid response from the API")
    st.session_state.history.append({
            "question": st.session_state['user_input'],
            "nlr": """
The data table returned provides information on the sales performance of different stores for this year and the previous year. The table includes columns such as STORE_ID, STORE_NAME, SALES_TY (sales for this year), and SALES_LY (sales for the previous year).\n\n
Looking at the data, we can observe that the sales for most stores vary between this year and the previous year. Some stores have seen an increase in sales, while others have experienced a decrease.\n\n
For example, stores like BRISTOL SUPERSTORE, CWMBRAN, and CARDIFF have seen an increase in sales this year compared to the previous year. On the other hand, stores like NEWPORT, CRIBBS CAUSEWAY, and SWANSEA have shown a decrease in sales.\n\n
It is also interesting to note that some stores have had significant changes in sales performance. For instance, stores like West End New, Budapest Arena Plaza, and Arkad Budapest have experienced a significant increase in sales this year compared to the previous year. Conversely, stores like Budapest Vaci Utca and Gyor Arkad have seen a significant decrease in sales.\n\n
Overall, the data table provides a comparison of sales performance across all stores for this year against the previous year, highlighting the varying trends in sales for different stores.
    """,
            "sql": "SELECT DISTINCT STORE_ID, STORE_NAME, SALES_TY, SALES_LY\nFROM claires_data.store_total;",
        })
    conn = connect_to_db(DB_NAME)
    result = execute_query("SELECT DISTINCT STORE_ID, STORE_NAME, SALES_TY, SALES_LY\nFROM claires_data.store_total;", conn)
    st.session_state['display_df_and_nlr'] = True
    st.session_state['last_result'] = result
    st.session_state['last_nlr'] = st.session_state.history[-1]["nlr"]
    
if st.session_state['display_df_and_nlr']:
    # Display DataFrame first
    st.dataframe(st.session_state['last_result'], height=200)
    
    # Delay the Natural Language Response by 5 seconds
    time.sleep(5)
    st.write(st.session_state['last_nlr'])
