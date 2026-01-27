import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Custom AEO Analyzer", layout="wide")

st.title("👔 India Men's Western Wear AI-Analyzer")
st.markdown("Track brand visibility across your own custom categories.")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("1. Selection & Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    brand_choice = st.selectbox("Select Brand", 
                                ["nobero.com", "bewakoof.com", "urbanofashion.com", "tigc.in"])
    
    # Category Input Mode
    input_mode = st.radio("Category Selection Mode", ["Auto-suggested", "Manual Entry"])
    
    brand_map = {
        "nobero.com": "men's joggers, gym t-shirts, oversized hoodies, training shorts",
        "bewakoof.com": "graphic t-shirts for men, cargo pants, oversized fit tees, varsity jackets",
        "urbanofashion.com": "slim fit jeans for men, casual chinos, denim jackets, distressed denim",
        "tigc.in": "solid polo t-shirts, basic crew neck tees, men's casual shirts, Henley shirts"
    }
    
    # Logic for manual vs auto entry
    if input_mode == "Manual Entry":
        categories_input = st.text_area("Type your categories (comma separated)", 
                                       placeholder="e.g. linen shirts, bootcut jeans, summer shorts")
    else:
        categories_input = st.text_area("Target Categories (Auto-suggested)", value=brand_map[brand_choice])
    
    num_queries = st.slider("Queries per Category", 2, 8, 3)

    if api_key:
        openai.api_key = api_key

# --- CORE LOGIC ---

def discover_prompts(categories, n):
    client = openai.OpenAI(api_key=api_key)
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    all_q = []
    for cat in cat_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI research assistant for the Indian men's Western fashion market."},
                {"role": "user", "content": f"Find {n} realistic non-branded queries Indian shoppers ask for: '{cat}'. One per line."}
            ]
        )
        all_q.extend(resp.choices[0].message.content.strip().splitlines())
    return [q.strip("-•1234567890. ") for q in all_q if q.strip()]

def check_presence(query, brand_name, brand_domain):
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Analyze the top 10 Indian brands for the query. Return: Rank | Brand | URL. End with 2 sentences of AEO advice for {brand_name}."},
                {"role": "user", "content": f"Query: {query}"}
            ]
        )
        output = resp.choices[0].message.content.strip()
        brand_name_clean = brand_domain.split(".")[0]
        present = "Yes" if brand_name_clean.lower() in output.lower() else "No"
        return {"Query": query, "Brand Present": present, "AI Context": output}
    except Exception as e:
        return {"Query": query, "Brand Present": "Error", "AI Context": str(e)}

# --- APP FLOW ---

if st.button("Run Custom AEO Scan"):
    if not api_key:
        st.error("Please enter your OpenAI API Key.")
    elif not categories_input:
        st.error("Please enter at least one category.")
    else:
        with st.status("Scanning Indian AI Landscape...") as status:
            st.write("🔎 Generating target prompts...")
            queries = discover_prompts(categories_input, num_queries)
            
            results = []
            bar = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Checking presence for: **{q}**")
                results.append(check_presence(q, brand_choice, brand_choice))
                bar.progress((i + 1) / len(queries))
            
            df = pd.DataFrame(results)
            st.session_state['results_df'] = df
            status.update(label="Scan Complete!", state="complete")

if 'results_df' in st.session_state:
    df = st.session_state['results_df']
    
    # Share of