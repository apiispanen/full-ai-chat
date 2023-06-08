import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
from htmlTemplates import chatbot_js, chatbot_html
from helpers import *
import openai
import socketio
import flask
import requests
from flask_app import *

import multiprocessing
flask_process = multiprocessing.Process(target=app)


from dotenv import load_dotenv

load_dotenv()

if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = None

from flask_socketio import SocketIO, emit

# Define the first row section
st.session_state.conversation = get_conversation_chain()

# ######## STEP 1: Define the chatbot ########

# Define the third row section
st.header("1. Test of chatbot")
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    prompt = data['prompt']
    response = handle_userstreaminginput(prompt)
    messages = [{"role": "user", "content": prompt}]
    # NOW RUN THE PROMPT:
    # ai_response(prompt)
    # response = openai.ChatCompletion.create(
    #     model='gpt-3.5-turbo',
    #     messages=messages,
    #     temperature=temperature,
    #     stream=True  # set stream=True
    # )
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta']  # extract the message
        socketio.emit('response', {"message": chunk_message})  # send the chunk message and result_dict to the client

# Wrapt the javascript as html code
my_html = f"{chatbot_js}{chatbot_html}"
html(my_html, height=800)

# st.header("Specialist Chatbot :books:")
user_question = st.text_input("Ask a question about your PDFs:")
if user_question:
    handle_userinput(user_question)


# Define the second row section
# ######## STEP 2: Configurations ########

# Define the second row section
st.header("2. Configurations")
temperature = st.slider("GPT Temperature", key="temperature", min_value=0.0, max_value=1.0, value=0.5)
uploaded_file = st.file_uploader("Upload Context PDFs", key="pdf-uploader", type=['pdf'])
models = ['gpt-3.5-turbo', 'model2', 'model3']
model_choice = st.selectbox('Model Selection',  models, key="model", index=0)
max_token = st.number_input('Max Token Selection', key="token", min_value=1, max_value=1000, value=500)

if st.button('Update Configuration'):
    requests.post('http://localhost:5000/configure', json={
        'temperature': temperature,
        'model': model_choice,
        'max_token': max_token
    })



# ####### STEP 3: Define the chatbot #######

st.header("3. Recent chats")
response = requests.get('http://localhost:5000/get_chat_history')
print(response.text)
df = pd.DataFrame(response.json())
st.table(df)


with st.sidebar:
    st.subheader("Your documents")
    pdf_docs = st.file_uploader(
        "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
    if st.button("Process"):
        with st.spinner("Processing"):
            # get pdf text
            raw_text = get_pdf_text(pdf_docs)

            # get the text chunks
            text_chunks = get_text_chunks(raw_text)

            # create vector store
            vectorstore = get_vectorstore(text_chunks)

            # create conversation chain
            st.session_state.conversation = get_conversation_chain(
                vectorstore)