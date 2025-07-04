# AgentInvest
What if you could ask an **AI Agent** to screen companies based on **your investment criteria**? Just Ask something like: **"Find AI-enabled healthcare companies with over $1B EBITDA"**

And get top matches as the ones shown below.

AgentInvest is a prototype project for building an AI-powered investment research assistant. 
It combines: 
- LangGraph based agents to parse, clarify and enrich a natural language query into a structured output ready for retrieval. 
- A retrieval index backed by Weaviate enabling vector and filter-based search.
- A Streamlit UI for user interactions and displaying results.
- Docker containerized services for modularity.

The repository contains scripts for loading company data, creating embeddings with OpenAI and running a FastAPI service that answers user queries about potential investments.

![image](https://github.com/user-attachments/assets/d0fdb430-fdec-44d2-a80a-343665bd83e6)
