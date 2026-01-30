import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="India Men's Western Wear AEO 2026", layout="wide", page_icon="👔")

st.title("👔 India Men's Western Wear AI-Analyzer (2026 Edition)")
st.markdown(f"Current Date: **{datetime.now().strftime('%B %d, %Y')}**")
st.markdown("Analyze brand visibility for **Western Wear** in the 2026 Indian market using Custom Categories.")

# --- 2. SIDEBAR SETUP ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter OpenAI API Key", type="password", help="Needed to run the AI analysis.")
    
    # Updated Brand Selection with Wrogn and Veirdo
    brand_choice = st.selectbox("Select Target Brand", 
                                ["wrogn.com", "veirdo.in", "nobero.com", "bewakoof.com", "urbanofashion.com", "tigc.in"])
    
    # Custom Category Mode
    input_mode = st.radio("Category Input Mode", ["Auto-suggested", "Manual Entry"])
    
    # Updated Brand-to-Category Mapping for 2026 Trends
    brand_map = {
        "wrogn.com": "slim fit denim jeans, quirky casual shirts, activewear jackets, slim fit chinos",
        "veirdo.in": "oversized graphic t-shirts, co-ord sets for men, acid wash tees, street style cargos",
        "nobero.com": "men's joggers, gym t-shirts, oversized hoodies, training shorts",
        "bewakoof.com": "graphic t-shirts for men, cargo pants, oversized fit tees, varsity jackets",
        "urbanofashion.com": "slim fit jeans for men, casual chinos, denim jackets, distressed denim",
        "tigc.in": "solid polo t-shirts, basic crew neck tees, men's casual shirts, Henley shirts"
    }
    
    if input_mode == "Manual Entry":
        categories_input = st.text_area("Enter your categories (comma separated)", 
                                        placeholder="e.g. linen shirts, bootcut jeans, denim shorts")
    else:
        categories_input = st.text_area("Target Categories (Auto-mapped)", value=brand_map.get(brand_choice, ""))
    
    # Expanded Query range from 5 to 100
    num_queries = st.slider("Queries per Category", 5, 100, 10)

    if api_key:
        openai.api_key = api_key

# --- 3. CORE LOGIC FUNCTIONS ---

def discover_prompts(categories, n):
    """Generates realistic 2026 Indian shopping queries."""
    client = openai.OpenAI(api_key=api_key)
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    all_q = []
    
    current_year = 2026 # Ensuring the prompt explicitly asks for 2026 data
    
    for cat in cat_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are an AI research assistant specializing in the {current_year} Indian Men's Western Wear market."},
                {"role": "user", "content": f"Find {n} non-branded, high-intent shopping queries Indian men ask in {current_year} for: '{cat}'. Focus on current 2026 trends like relaxed silhouettes and sustainable fabrics. One per line."}
            ]
        )
        all_q.extend(resp.choices[0].message.content.strip().splitlines())
    return [q.strip("-•1234567890. ") for q in all_q if q.strip()]

def check_presence(query, brand_choice):
    """Analyzes the AI's response to check if the brand is recommended in 2026."""
    client = openai.OpenAI(api_key=api_key)
    brand_name_clean = brand_choice.split(".")[0]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a shopping assistant in January 2026. Analyze the top 10 Indian brands for this query. Format as: Rank | Brand | URL. End with AEO advice for the brand to rank better in 2026."},
                {"role": "user", "content": f"Query: {query}"}
            ]
        )
        output = resp.choices[0].message.content.strip()
        present = "Yes" if brand_name_clean.lower() in output.lower() else "No"
        return {"Query": query, "Brand Present": present, "AI Analysis": output}
    except Exception as e:
        return {"Query": query, "Brand Present": "Error", "AI Analysis": str(e)}

# --- 4. EXECUTION ENGINE ---

if st.button("🚀 Run India AEO Scan (2026)"):
    if not api_key:
        st.error("❌ Please enter your OpenAI API Key in the sidebar.")
    elif not categories_input:
        st.error("❌ Please provide at least one category.")
    else:
        with st.status("🔍 Scanning 2026 Indian AI Market...", expanded=True) as status:
            st.write("Generating 2026 target shopping queries...")
            queries = discover_prompts(categories_input, num_queries)
            
            results = []
            progress_bar = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Analyzing Presence for: **{q}**")
                res = check_presence(q, brand_choice)
                results.append(res)
                progress_bar.progress((i + 1) / len(queries))
            
            st.session_state['results_df'] = pd.DataFrame(results)
            status.update(label="✅ 2026 Scan Complete!", state="complete", expanded=False)

# --- 5. RESULTS DISPLAY ---

if 'results_df' in st.session_state and st.session_state['results_df'] is not None:
    df = st.session_state['results_df']
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        sov = (df[df['Brand Present'] == "Yes"].shape[0] / len(df)) * 100
        st.metric(label=f"2026 Share of Voice (SOV): {brand_choice}", value=f"{sov:.1f}%")
    
    with col2:
        st.write("### AI Visibility Distribution (2026)")
        fig = px.pie(df, names="Brand Present", 
                     color="Brand Present", 
                     color_discrete_map={"Yes":"#27AE60", "No":"#E74C3C", "Error":"#95A5A6"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 2026 AI Intelligence & Advice")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download 2026 Report", data=csv, file_name=f"aeo_2026_{brand_choice}.csv", mime="text/csv")
else:
    st.info("💡 Enter your settings and click the button above to start the 2026 analysis.")
