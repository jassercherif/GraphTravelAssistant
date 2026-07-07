import requests
import streamlit as st

API_URL = "http://localhost:8000/chat/"

st.set_page_config(page_title="Travel AI Agent", page_icon="🌍", layout="centered")
st.title("🌍 Travel AI Agent")
st.caption("GraphRAG-powered travel assistant — Neo4j + vector search + LLM")

# Keep chat history across reruns (Streamlit reruns the script on every
# interaction, so without session_state the conversation would reset
# every time you ask a new question)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past turns
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# New input
query = st.chat_input("Ask about a destination, e.g. 'What is the Louvre?'")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(API_URL, json={"query": query}, timeout=90)
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("answer", "No answer returned.")
            except requests.exceptions.Timeout:
                answer = "The assistant is taking too long to respond. Please try again."
            except requests.exceptions.RequestException as e:
                answer = f"Couldn't reach the API: {e}"

        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

with st.sidebar:
    st.subheader("About")
    st.write("Backend: FastAPI + Neo4j GraphRAG pipeline.")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()