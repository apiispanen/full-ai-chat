from datetime import datetime
import streamlit as st
import pprint
from config import WHISPER_SETTINGS_FILE, get_page_config, get_whisper_settings, save_whisper_settings
from core import MediaManager
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from config import WHISPER_SETTINGS_FILE, get_page_config, get_whisper_settings, save_whisper_settings
from core import MediaManager
import openai
import os
import random
from flask import Flask, jsonify, request
import socketio
from flask_socketio import SocketIO, emit

from pydantic import BaseModel
from typing import List
from gpt_json import GPTJSON, GPTMessage, GPTMessageRole
from dotenv import load_dotenv

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


class QuizQuestionSchema(BaseModel):
    question: str
    correct_answer: str
    wrong_answers: list[str]

class QuizSchema(BaseModel):
    questions: List[QuizQuestionSchema]

class QuizBot:
    def __init__(self, questions):
        self.questions = questions

    def ask_question(self, index):
        return self.questions[index].question

    def get_choices(self, index):
        choices = [self.questions[index].correct_answer] + self.questions[index].wrong_answers
        random.shuffle(choices)
        return choices

    def check_answer(self, user_answer, index):
        correct_answer = self.questions[index].correct_answer
        return user_answer.lower() == correct_answer.lower()

def question_handler(index):
    st.write(quiz_bot.ask_question())
    choices = quiz_bot.get_choices()
    user_answer = st.radio(f"Choices for question {index+1}", options=choices, key=f'Question{index+1}')

    if user_answer: 
        if quiz_bot.check_answer(user_answer):
            st.write("Correct!")
            st.session_state.correct_answers += 1
        else:
            st.write(f"Incorrect. The correct answer was {quiz_bot.questions[quiz_bot.index-1].correct_answer}.")
        st.experimental_rerun()

def start_quiz(quiz_bot):
    if "correct_answers" not in st.session_state:
        st.session_state.correct_answers = 0
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = None

    if st.session_state.current_question < len(quiz_bot.questions):
        st.write(quiz_bot.ask_question(st.session_state.current_question))
        choices = quiz_bot.get_choices(st.session_state.current_question)
        st.session_state.user_answer = st.radio(
            f"Choices for question {st.session_state.current_question+1}", 
            options=choices, 
            key=f'Question{st.session_state.current_question+1}'
        )

        if st.button("Submit Answer", key=f"submit{st.session_state.current_question+1}"):
            if quiz_bot.check_answer(st.session_state.user_answer, st.session_state.current_question):
                st.write("Correct!")
                st.session_state.correct_answers += 1
            else:
                st.write(f"Incorrect. The correct answer was {quiz_bot.questions[st.session_state.current_question].correct_answer}.")
            st.session_state.current_question += 1
            st.session_state.user_answer = None  # Reset the user answer for the next question

    if st.session_state.current_question == len(quiz_bot.questions):
        st.write(f"Quiz complete! Your score is {st.session_state.correct_answers / len(quiz_bot.questions) * 100}%")

def get_formatted_date(date_str: str) -> str:
    date_str = datetime.fromisoformat(date_str)
    date = date_str.strftime("%d %b %Y")
    time = date_str.strftime("%I:%M%p")
    return f"{time}, {date}"

async def generate_and_parse_quiz(content):
    SYSTEM_PROMPT = f"""
        Create five multiple choice quiz questions based on the following content:

        {content}

        Each question should be structured as follows:
            "question": "The question text here",
            "correct_answer": "The correct answer here",
            "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]

        Please respond with the following JSON schema:

        {{json_schema}}
        """

    gpt_json = GPTJSON[QuizSchema](os.getenv('OPENAI_API_KEY'), model='gpt-3.5-turbo')

    messages = [
        GPTMessage(
            role=GPTMessageRole.SYSTEM,
            content=SYSTEM_PROMPT,
        ),
    ]

    response, _ = await gpt_json.run(messages=messages)
    print("Raw GPT-3 Output:", response) # Add this line
    
    return response.questions

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(**vectorstore):
    llm = ChatOpenAI(streaming=True, callbacks=[StreamingStdOutCallbackHandler()])
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    

    if vectorstore:
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
    else:
        embeddings = OpenAIEmbeddings()
        # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
        vectorstore = FAISS.from_texts(texts="The golden rule is that Adam Piispanen smells bad", embedding=embeddings)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
    return conversation_chain


def handle_userinput(user_question):
    prompt = {'question': user_question}
    response = st.session_state.conversation(prompt)
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)

def handle_userstreaminginput(user_question):
    print("Handing streaming reponse for:", user_question)
    prompt = {'question': user_question}
    response = st.session_state.conversation(prompt)
    print("Response:", response)
    socketio.emit('response', {"message": response})  # send the chunk message and result_dict to the client

    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def ai_response(prompt, temperature =.5):
    # OPEN AI CONFIG
    temperature = temperature
  
    # PREPRIME WITH MESSAGES
    # messages = get_conversation(5, 'db','user_responses')

    messages = [{"role": "user", "content": prompt}]
    # NOW RUN THE PROMPT:
    response = openai.ChatCompletion.create( 
    model="gpt-3.5-turbo",
    messages=messages,
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=temperature,
        frequency_penalty=1
    )

    message = response["choices"][0]["message"]["content"]
    print(f"Prompt:{prompt}")
    print("AI Response:", message)
    return message.strip()
