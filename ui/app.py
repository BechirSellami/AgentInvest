import os
import requests
import streamlit as st

from dotenv import load_dotenv
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")

st.subheader("AI Screening Agent - What companies are you looking for?")

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
# margin-bottom: 10px;
for role, content in st.session_state.history:
    with st.chat_message(role):
        if role == "user":
            st.markdown(
                f"""
                <div style="background-color:#e6f2ff; padding: 12px 18px; border-radius: 8px; font-size: 16px; margin-bottom: 20px;">
                    <strong>{user_input}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            if isinstance(content, dict):
                logger.info("Agent response: %s", content)

                docs = content.get("retrieved_docs")
                logger.info("Retrieved documents: %s", docs)
                if docs:
                    st.subheader("Top matches for your query")
                    st.markdown(
                        "<p style='font-size: 13px; color: gray; margin-top: -10px;'>"
                        "Ranked by relevance using vector + filter-based search"
                        "</p>",
                        unsafe_allow_html=True
                    )
                    for doc in docs:
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"### {doc.get('name', 'Unknown')} ({doc.get('ticker', '-')})")
                                st.markdown(f"**Sector**: {doc.get('sector', '-')}")
                                st.markdown(f"**Country**: {doc.get('country', '-')}")
                                st.markdown(f"**Market Cap**: ${doc.get('market_cap_musd', 0)/1000:,.1f}B")
                                st.markdown(f"**EBITDA**: ${doc.get('ebitda_musd', 0)/1000:,.1f}B")
                                st.markdown(f"**Revenue Growth**: {doc.get('rev_growth_pct', 0)*100:.0f}%")
                            with col2:
                                # Show relevance score
                                score = (1 - doc.get('_distance', 1))
                                st.metric(label="Relevance Score", value=f"{score:.2f}")
            else:
                st.write(content)
                st.write(content)

st.markdown(
        "<hr style='margin-top: 40px; margin-bottom: 5px;'>"
        "<p style='text-align: center; font-size: 12px; color: gray;'>"
        "🔍 Powered by <strong>InvestAgent</strong> – An agentic AI prototype for thematic stock screening"
        "</p>",
        unsafe_allow_html=True
    )    