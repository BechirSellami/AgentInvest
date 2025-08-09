import os
import requests
import streamlit as st

st.set_page_config(
    page_title="AI Screening Agent",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
      /* increase the maximum width of the main content area */
      .main .block-container {
        max-width: 900px;
        padding-left: 1rem;
        padding-right: 1rem;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# override any max‑width on chat_input / textarea
st.markdown(
    """
    <style>
      /* make chat_input full‑width */
      .stChatInput > div,
      .stTextArea > textarea {
        width: 100% !important;
        max-width: 100% !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# force chat_input to exactly match our 900px container
st.markdown(
    """
    <style>
      /* target the chat widget’s wrapper by its test‑id */
      div[data-testid="stChatInput"] {
        max-width: 900px !important;
        margin: 0 auto !important;
      }
      div[data-testid="stChatInput"] > div {
        width: 100% !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
API_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service")

st.subheader("AI Screening Agent - What companies are you looking for?")

if "history" not in st.session_state:
    st.session_state.history = []
if "full_query" not in st.session_state:
    st.session_state.full_query = ""

user_input = st.chat_input("Enter your query")

if user_input:
    if st.session_state.full_query:
        st.session_state.full_query += "\n" + user_input
    else:
        st.session_state.full_query = user_input

    try:
        response = requests.post(f"{API_URL}/query", json={"query": st.session_state.full_query})
        data = response.json() if response.ok else {"error": response.text}
    except Exception as exc:
        data = {"error": str(exc)}

    st.session_state.history.append(("user", user_input))
    st.session_state.history.append(("agent", data))

    if data.get("need_clarification"):
        st.info("The agent needs more information. Please clarify your query.")
    else:
        st.session_state.full_query = ""

for role, content in st.session_state.history:
    with st.chat_message(role):
        if role == "user":
            st.markdown(
                f"""
                <div style="background-color:#e6f2ff; padding:12px 18px; border-radius:8px; font-size:16px; margin-bottom:20px;">
                  <strong>{user_input}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            if isinstance(content, dict):
                logger.info("Agent response: %s", content)
                docs = content.get("retrieved_docs", [])
                if not docs:
                    st.subheader("No companies match your query")
                else:
                    st.subheader("Top matches for your query")
                    st.markdown(
                        "<p style='font-size: 13px; color: gray; margin-top: -10px;'>"
                        "Ranked by relevance using vector + filter-based search"
                        "</p>",
                        unsafe_allow_html=True
                    )
                    for doc in docs:
                        if doc.get("_relevance", 0.0) > 0.001:
                            with st.container(border=True):
                                # ─── TOP ROW: Name + Score ───
                                name_col, score_col = st.columns([6, 1])
                                with name_col:
                                    st.markdown(f"## {doc.get('name','Unknown')} ({doc.get('ticker','-')})")
                                
                                # ── inside the per-doc loop ──────────────────────────────────────────────
                                with score_col:
                                    # _relevance is already a 0–1 score (higher is better)
                                    score = doc.get("_relevance", 0.0)          # no inversion
                                    score_col.markdown(
                                        f"""
                                        <div style="text-align: right;">
                                        <div style="font-size:0.85em; color:#6c757d; margin-bottom:0.3em;">
                                            Relevance&nbsp;Score
                                        </div>
                                        <div style="font-size:2em; font-weight:600; line-height:1;">
                                            {score:.2f}
                                        </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                                # ─── SECOND ROW: Sector/Country/Themes | Financials | (empty) ───
                                col1, col2, col3 = st.columns([3, 2, 1])
                                with col1:
                                    st.markdown(f"**Sector**: {doc.get('sector','-')}")
                                    st.markdown(f"**Country**: {doc.get('country','-')}")
                                    themes = doc.get("themes", [])
                                    if themes:
                                        st.markdown(f"**Services**: {', '.join(themes)}")
                                with col2:
                                    st.markdown(f"**Market Cap**: ${doc.get('market_cap_musd',0)/1000:,.1f} B")
                                    st.markdown(f"**EBITDA**: ${doc.get('ebitda_musd',0)/1000:,.1f} B")
                                    st.markdown(f"**Revenue Growth**: {doc.get('rev_growth_pct',0):.0f}%")
                                # col3 left empty for spacing

                                # ─── FULL‑WIDTH SUMMARY BELOW ───
                                summary_text = doc.get("summary") or doc.get("description", "")
                                if summary_text:
                                    #st.markdown("<br/>", unsafe_allow_html=True)
                                    with st.expander("Summary"):
                                        st.write(summary_text)
                            st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)

st.markdown(
    "<hr style='margin-top:40px; margin-bottom:5px;'>"
    "<p style='text-align:center; font-size:12px; color:gray;'>"
    "🔍 Powered by <strong>InvestAgent</strong> – An agentic AI prototype for thematic stock screening"
    "</p>",
    unsafe_allow_html=True
)