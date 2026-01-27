import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Men's Fashion AEO Insights", layout="wide")

st.title("👔 Men's Fashion AI-Visibility Analyzer")
st.markdown("Monitor how your apparel brand appears in AI shopping assistants.")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("1. Brand & Campaign Settings")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    
    # User Request: Option 1 - Brand Name
    brand_name = st.text_input("Brand Name", value="Urbano Fashion")
    
    # User Request: Option 2 - URL
    brand_domain = st.text_input("Brand Domain", value="urbanofashion.com")
    
    # User Request: Option 3 - Categories
    categories_input = st.text_area("Target Categories (Comma Separated)", 
                                   value="men's slim fit jeans, casual shirts for men, oversized t-shirts, ethnic wear for men")
    
    num_queries_per_cat = st.slider("Queries per Category", 2, 10, 5)
    
    if api_key:
        openai.api_key = api_key

# --- CORE FUNCTIONS ---

def discover_mens_prompts(brand, categories, n):
    """Generates non-branded men's fashion queries based on input categories."""
    client = openai.OpenAI(api_key=api_key)
    category_list = [c.strip() for c in categories.split(",")]
    
    all_queries = []
    for cat in category_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI market research assistant for the US/India men's fashion market."},
                {"role": "user", "content": f"Find {n} non-branded, high-intent shopping queries for the category: '{cat}'. Return only the list, one per line."}
            ]
        )
        lines = resp.choices[0].message.content.strip().splitlines()
        all_queries.extend([ln.strip("-•1234567890. ") for ln in lines if ln.strip()])
    return all_queries

def analyze_fashion_query(query, brand_name, brand_domain):
    """Analyzes visibility and provides styling/AEO advice."""
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are an AI stylist. Rank top 10 brands for the query. Format: Rank | Brand | URL. Then provide advice for {brand_name}."},
                {"role": "user", "content": f"Query: {query}"}
            ]
        )
        output = resp.choices[0].message.content.strip()
        
        appears = "Yes" if brand_name.lower() in output.lower() else "No"
        
        # Simple extraction logic
        return {
            "Query": query,
            "Brand Appears": appears,
            "Details": output
        }
    except Exception as e:
        return {"Query": query, "Brand Appears": "Error", "Details": str(e)}

# --- MAIN INTERFACE ---

if st.button("Generate & Analyze Men's Fashion Prompts"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar.")
    else:
        with st.status("Gathering AI Intelligence...", expanded=True) as status:
            st.write("🏃 Generating prompts based on your categories...")
            queries = discover_mens_prompts(brand_name, categories_input, num_queries_per_cat)
            
            results = []
            progress = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Analyzing: {q}")
                results.append(analyze_fashion_query(q, brand_name, brand_domain))
                progress.progress((i + 1) / len(queries))
            
            df = pd.DataFrame(results)
            st.session_state['fashion_results'] = df
            status.update(label="Analysis Complete!", state="complete")

if 'fashion_results' in st.session_state:
    df = st.session_state['fashion_results']
    
    # Visibility Chart
    st.subheader("Visibility Summary")
    fig = px.pie(df, names="Brand Appears", title="Brand Appearance in AI Answers",
                 color="Brand Appears", color_discrete_map={"Yes":"#2ECC71", "No":"#E74C3C", "Error":"#95A5A6"})
    st.plotly_chart(fig)
    
    # Results Table
    st.subheader("Detailed Breakdown")
    st.dataframe(df, use_container_width=True)
