from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import openai
import json
import streamlit as st
from helpers import handle_userstreaminginput,get_conversation_chain
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
from dotenv import load_dotenv

load_dotenv()
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = None
st.session_state.conversation = get_conversation_chain()

temperature = .7
# st.session_state.conversation = get_conversation_chain()

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    # replace this with actual logic to get chat history from the database
    st.write("sup dude")
    print('*********************get_chat_history*********************')
    return jsonify({
        'chat_id': [1, 2, 3, 4],
        'message': ['hello', 'hi', 'hey', 'howdy'],
        'time': ['10:00', '10:01', '10:02', '10:03']
    })

@app.route('/configure', methods=['POST'])
def configure():
    data = request.get_json()
    temperature = data.get('temperature')
    model = data.get('model')
    max_token = data.get('max_token')
    # replace this with actual logic to configure the model
    return jsonify({'status': 'Configuration updated successfully'})

@socketio.on('message')
def handle_message(data):
    print('received message: ', data)
    # conversation = get_conversation_chain()
    prompt = data['prompt']
    # response = handle_userstreaminginput(prompt, conversation)
    messages = [{"role": "user", "content": prompt}]
    # NOW RUN THE PROMPT:
    # ai_response(prompt)
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=temperature,
        stream=True  # set stream=True
    )
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta']  # extract the message
        socketio.emit('response', {"message": chunk_message})  # send the chunk message and result_dict to the client


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
