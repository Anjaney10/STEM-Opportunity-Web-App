import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
import time

st.set_page_config(
    page_title="Global STEM Opportunities",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Global STEM PhD Scholarships & Internships Hub")
st.markdown("**Live data + curated opportunities** for STEM students worldwide")

# -------------------------- DATA & SCRAPING --------------------------
CACHE_FILE = "opportunities_cache.json"
CACHE_EXPIRY_HOURS = 12

@st.cache_data(ttl=3600*12)  # Streamlit built-in caching
def load_opportunities():
    # Static high-quality opportunities (updated 2026)
    static = [
        {
            "id": 1,
            "title": "NSF Graduate Research Fellowship Program (GRFP)",
            "type": "PhD Scholarship",
            "country": "USA",
            "latitude": 37.0902,
            "longitude": -95.7129,
            "deadline": "Nov 10–14, 2025 (varies by field)",
            "award_amount": "$34,000/year stipend + tuition",
            "eligibility": "US citizens/permanent residents pursuing STEM PhD",
            "description": "Highly prestigious fellowship supporting outstanding graduate students in STEM.",
            "link": "https://www.nsfgrfp.org"
        },
        {
            "id": 2,
            "title": "DAAD RISE Germany Research Internships",
            "type": "Internship",
            "country": "Germany",
            "latitude": 51.1657,
            "longitude": 10.4515,
            "deadline": "Nov 30, 2025",
            "award_amount": "€934+/month + benefits",
            "eligibility": "International undergrad/master students in STEM",
            "description": "8–12 week paid research internships at German universities and institutes.",
            "link": "https://www.daad.de/rise"
        },
        {
            "id": 3,
            "title": "Fulbright Foreign Student Program",
            "type": "PhD Scholarship",
            "country": "Multiple",
            "latitude": 20.0,
            "longitude": 0.0,
            "deadline": "Varies by country",
            "award_amount": "Full funding",
            "eligibility": "Varies by country",
            "description": "Graduate study and research opportunities in the US.",
            "link": "https://fulbrightprogram.org"
        },
        {
            "id": 4,
            "title": "Google PhD Fellowship",
            "type": "PhD Fellowship",
            "country": "Multiple",
            "latitude": 37.0902,
            "longitude": -95.7129,
            "deadline": "Varies (typically Oct–Nov)",
            "award_amount": "$10,000+/year + mentorship",
            "eligibility": "PhD students in CS, AI, ML and related fields",
            "description": "Supports promising PhD candidates globally.",
            "link": "https://research.google/outreach/phd-fellowship/"
        },
        {
            "id": 5,
            "title": "CERN Summer Student Programme",
            "type": "Internship",
            "country": "Switzerland",
            "latitude": 46.8182,
            "longitude": 8.2275,
            "deadline": "Typically March",
            "award_amount": "Paid stipend + travel + housing",
            "eligibility": "Bachelor/Master students in physics, engineering, CS",
            "description": "Hands-on research at CERN.",
            "link": "https://careers.cern/summer-student-programme"
        },
    ]

    # Try to get fresh data from Zintellect
    try:
        url = "https://www.zintellect.com/catalog"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; STEMOppBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        opportunities = []
        # Basic extraction - Zintellect is dynamic, so this captures some visible items
        for item in soup.find_all("a", href=True):
            text = item.get_text(strip=True)
            if any(kw in text for kw in ["2026", "Internship", "Fellowship", "Scholar"]):
                opportunities.append({
                    "id": len(static) + len(opportunities) + 1,
                    "title": text[:100],
                    "type": "Internship/Fellowship",
                    "country": "USA",
                    "latitude": 37.0902,
                    "longitude": -95.7129,
                    "deadline": "Varies - Check site",
                    "award_amount": "Stipend varies",
                    "eligibility": "STEM students",
                    "description": "Government-funded opportunity via Zintellect.",
                    "link": "https://www.zintellect.com/catalog"
                })
            if len(opportunities) >= 8:
                break
    except:
        opportunities = []

    df = pd.DataFrame(static + opportunities)
    return df

df = load_opportunities()

# -------------------------- SIDEBAR FILTERS --------------------------
st.sidebar.header("🔍 Filters")

type_options = ["All"] + sorted(df["type"].unique().tolist())
selected_type = st.sidebar.selectbox("Opportunity Type", type_options)

search_term = st.sidebar.text_input("Keyword Search", placeholder="AI, Biology, Deadline...")

# -------------------------- FILTERED DATA --------------------------
filtered_df = df.copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["type"] == selected_type]

if search_term:
    mask = (
        filtered_df["title"].str.contains(search_term, case=False, na=False) |
        filtered_df["description"].str.contains(search_term, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

# -------------------------- LAYOUT --------------------------
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🌍 Interactive World Map")
    if filtered_df.empty:
        st.warning("No opportunities match your filters.")
    else:
        fig = px.scatter_geo(
            filtered_df,
            lat="latitude",
            lon="longitude",
            hover_name="title",
            hover_data=["country", "deadline", "award_amount"],
            color="type",
            title="STEM Opportunities Worldwide",
            size_max=25,
            projection="natural earth"
        )
        fig.update_layout(height=650, margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 Opportunities")
    display_cols = ["title", "type", "country", "deadline", "award_amount"]
    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Opportunity"),
            "award_amount": st.column_config.TextColumn("Award"),
        }
    )

# -------------------------- DETAILS SECTION --------------------------
st.markdown("---")
st.subheader("🔎 Opportunity Details")

if not filtered_df.empty:
    selected_id = st.selectbox(
        "Select an opportunity to view details",
        options=filtered_df["id"],
        format_func=lambda x: filtered_df[filtered_df["id"] == x]["title"].iloc[0]
    )
    
    opp = filtered_df[filtered_df["id"] == selected_id].iloc[0]
    
    st.markdown(f"### {opp['title']}")
    st.markdown(f"**Type:** {opp['type']}  |  **Location:** {opp['country']}")
    st.markdown(f"**Deadline:** {opp['deadline']}")
    st.markdown(f"**Award:** {opp['award_amount']}")
    st.markdown(f"**Eligibility:** {opp['eligibility']}")
    st.markdown(f"**Description:** {opp['description']}")
    
    st.markdown(f"[🔗 Apply / Learn More]({opp['link']})")
else:
    st.info("No results to display details.")

# -------------------------- FOOTER --------------------------
st.caption("Data combines curated programs + live scraping from public sources like Zintellect. "
           "Always verify deadlines on official websites. Built with Streamlit.")

# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
