import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")

st.title("AgentInvest Query Interface")

if "history" not in st.session_state:
    st.session_state.history = []
if "full_query" not in st.session_state:
    st.session_state.full_query = ""

user_input = st.chat_input("Enter your query")

if user_input:
    # accumulate input in case clarification is required
    if st.session_state.full_query:
        st.session_state.full_query += "\n" + user_input
    else:
        st.session_state.full_query = user_input
    
    try:
        response = requests.post(f"{API_URL}/query", json={"query": st.session_state.full_query})
        if response.ok:
            data = response.json()
        else:
            data = {"error": response.text}
            
    except Exception as exc:
        data = {"error": str(exc)}

    st.session_state.history.append(("user", user_input))
    st.session_state.history.append(("agent", data))

    if data.get("need_clarification"):
        st.info("The agent needs more information. Please clarify your query.")
    else:
        # reset accumulated query when complete
        st.session_state.full_query = ""

for role, content in st.session_state.history:
    with st.chat_message(role):
        if role == "user":
            st.write(content)
        else:
            if isinstance(content, dict):
                st.json(content)
                with st.expander("Graph state"):
                    st.json(content)

                docs = content.get("retrieved_docs")
                if docs:
                    st.write("Retrieved documents:")
                    st.table(docs)
            else:
                st.write(content)
                st.write(content)