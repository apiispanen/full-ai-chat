import streamlit as st
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
from config import WHISPER_SETTINGS_FILE, get_page_config, get_whisper_settings, save_whisper_settings
from core import MediaManager
from helpers import *



# Session states
# --------------
# NOTE: This is repeated since direct landing on this page will throw an error
# Add whisper settings to session state
if "whisper_params" not in st.session_state:
    st.session_state.whisper_params = get_whisper_settings()


if "media_manager" not in st.session_state:
    st.session_state.media_manager = MediaManager()

# Alias for session state media manager
media_manager = st.session_state.media_manager


# Session states
# --------------
# NOTE: This is repeated since direct landing on this page will throw an error
# Add whisper settings to session state
if "whisper_params" not in st.session_state:
    st.session_state.whisper_params = get_whisper_settings()


load_dotenv()
st.write(css, unsafe_allow_html=True)

if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = None

st.header("Specialist Chatbot :books:")
user_question = st.text_input("Ask a question about your PDFs:")
if user_question:
    handle_userinput(user_question)

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

