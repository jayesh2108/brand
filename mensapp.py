import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="India Men's Western Wear AEO", layout="wide", page_icon="👔")

st.title("👔 India Men's Western Wear AI-Analyzer")
st.markdown("Analyze brand visibility for **Western Wear** in the Indian market using Custom Categories.")

# --- 2. SIDEBAR SETUP ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter OpenAI API Key", type="password", help="Needed to run the AI analysis.")
    
    # Brand Selection
    brand_choice = st.selectbox("Select Target Brand", 
                                ["nobero.com", "bewakoof.com", "urbanofashion.com", "tigc.in"])
    
    # Custom Category Mode
    input_mode = st.radio("Category Input Mode", ["Auto-suggested", "Manual Entry"])
    
    # Brand-to-Category Mapping (India Western Wear Focus)
    brand_map = {
        "nobero.com": "men's joggers, gym t-shirts, oversized hoodies, training shorts",
        "bewakoof.com": "graphic t-shirts for men, cargo pants, oversized fit tees, varsity jackets",
        "urbanofashion.com": "slim fit jeans for men, casual chinos, denim jackets, distressed denim",
        "tigc.in": "solid polo t-shirts, basic crew neck tees, men's casual shirts, Henley shirts"
    }
    
    if input_mode == "Manual Entry":
        categories_input = st.text_area("Enter your categories (comma separated)", 
                                       placeholder="e.g. linen shirts, bootcut jeans, denim shorts")
    else:
        categories_input = st.text_area("Target Categories (Auto-mapped)", value=brand_map[brand_choice])
    
    num_queries = st.slider("Queries per Category", 2, 5, 3)

    if api_key:
        openai.api_key = api_key

# --- 3. CORE LOGIC FUNCTIONS ---

def discover_prompts(categories, n):
    """Generates realistic Indian shopping queries for Western wear."""
    client = openai.OpenAI(api_key=api_key)
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    all_q = []
    for cat in cat_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI research assistant specializing in the Indian Men's Western Wear (Non-Ethnic) market."},
                {"role": "user", "content": f"Find {n} non-branded, high-intent shopping queries Indian men ask for: '{cat}'. One per line."}
            ]
        )
        all_q.extend(resp.choices[0].message.content.strip().splitlines())
    return [q.strip("-•1234567890. ") for q in all_q if q.strip()]

def check_presence(query, brand_choice):
    """Analyzes the AI's response to check if the brand is recommended."""
    client = openai.OpenAI(api_key=api_key)
    brand_name_clean = brand_choice.split(".")[0]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze the top 10 Indian brands for this query. Format as: Rank | Brand | URL. End with AEO advice."},
                {"role": "user", "content": f"Query: {query}"}
            ]
        )
        output = resp.choices[0].message.content.strip()
        present = "Yes" if brand_name_clean.lower() in output.lower() else "No"
        return {"Query": query, "Brand Present": present, "AI Analysis": output}
    except Exception as e:
        return {"Query": query, "Brand Present": "Error", "AI Analysis": str(e)}

# --- 4. EXECUTION ENGINE ---

if st.button("🚀 Run India AEO Scan"):
    if not api_key:
        st.error("❌ Please enter your OpenAI API Key in the sidebar.")
    elif not categories_input:
        st.error("❌ Please provide at least one category.")
    else:
        # Step 1: Discover Prompts
        with st.status("🔍 Scanning Indian AI Market...", expanded=True) as status:
            st.write("Generating target shopping queries...")
            queries = discover_prompts(categories_input, num_queries)
            
            # Step 2: Analyze Presence
            results = []
            progress_bar = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Analyzing Presence for: **{q}**")
                res = check_presence(q, brand_choice)
                results.append(res)
                progress_bar.progress((i + 1) / len(queries))
            
            # Save results to session state so they persist
            st.session_state['results_df'] = pd.DataFrame(results)
            status.update(label="✅ Scan Complete!", state="complete", expanded=False)

# --- 5. RESULTS DISPLAY (DASHBOARD) ---

# This section stays on screen as long as data exists in the session
if 'results_df' in st.session_state and st.session_state['results_df'] is not None:
    df = st.session_state['results_df']
    
    st.divider()
    
    # Metrics Row
    col1, col2 = st.columns(2)
    with col1:
        sov = (df[df['Brand Present'] == "Yes"].shape[0] / len(df)) * 100
        st.metric(label=f"Share of Voice (SOV) for {brand_choice}", value=f"{sov:.1f}%")
    
    with col2:
        st.write("### AI Visibility Distribution")
        fig = px.pie(df, names="Brand Present", 
                     color="Brand Present", 
                     color_discrete_map={"Yes":"#27AE60", "No":"#E74C3C", "Error":"#95A5A6"})
        st.plotly_chart(fig, use_container_width=True)

    # Detailed Table
    st.subheader("📋 Detailed AI Intelligence & Advice")
    st.dataframe(df, use_container_width=True)

    # Download Option
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report as CSV", data=csv, file_name=f"aeo_report_{brand_choice}.csv", mime="text/csv")

else:
    st.info("💡 Enter your settings and click the button above to start the analysis.")