import streamlit as st
import pandas as pd
import requests
import json
import time
import textwrap
import numpy as np
import pydeck as pdk

# --- 1. HELPER: HTML GENERATOR ---
def create_doctor_card(name, spec, hosp, loc, rating, reviews, exp, fees, img_url, link, is_optimal=False):
    card_class = "doctor-card optimal-card" if is_optimal else "doctor-card"
    
    if not img_url:
        img_url = "https://via.placeholder.com/70"
        
    link_html = ""
    if link:
        if is_optimal:
            link_html = f"<div style='margin-top:10px;'><a href='{link}' target='_blank' class='book-btn'>View Profile & Book</a></div>"
        else:
            link_html = f"<div style='margin-top:5px;'><a href='{link}' target='_blank' style='color:var(--primary-color); font-weight:bold; text-decoration:none;'>🔗 View Profile</a></div>"

    html = f"""
    <div class="{card_class}">
        <img src="{img_url}" class="profile-img">
        <div style="flex-grow: 1; padding-left: 15px;">
            <h3 style="margin:0; font-size:1.2em;">{name}</h3>
            <p class="sub-text" style="margin:0;">{spec} • {hosp}</p>
            <p class="sub-text" style="margin:0; font-size:0.85em; opacity:0.7;">📍 {loc}</p>
            {link_html}
        </div>
        <div style="text-align:right; min-width: 130px; border-left: 1px solid rgba(128,128,128,0.2); padding-left: 15px;">
            <div style="margin-bottom:5px;">
                <span style="color:#28a745; font-weight:bold; font-size:1.1em;">{rating}%</span> <span class="label">Satisfied</span>
            </div>
            <div class="sub-text" style="margin-bottom:5px;"><strong>{reviews}</strong> Reviews</div>
             <div class="sub-text" style="margin-bottom:5px;"><strong>{exp}</strong> Yrs Exp</div>
            <div class="price-tag">₹{fees}</div>
        </div>
    </div>
    """
    return html.replace("\n", "")

# --- 2. API FETCHING ---
def fetch_data(city, keyword, page):
    base_url = "https://www.practo.com/marketplace-api/dweb/search/provider/v2"
    q_param = [{"word": keyword, "autocompleted": True, "category": "subspeciality"}]
    
    params = {
        "city": city, "page": page, "q": json.dumps(q_param), "results_type": "doctor",
        "url_path": "/search/doctors", "ad_limit": 2, "platform": "desktop_web",
        "topaz": "true", "reach_version": "v4", "enable_partner_listing": "true",
        "placement": "DOCTOR_SEARCH", "show_new_reach_card": "true",
        "tracking_id": "81020639-7184-4756-88b3-d77b5ebe14a8" 
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

# --- 3. PARSING ---
def parse_doctors(json_data, search_term):
    doctors_list = []
    try:
        entities = json_data.get("doctors", {}).get("entities", {})
        for doc_id, data in entities.items():
            raw_url = data.get("profile_url", "")
            full_url = f"https://www.practo.com{raw_url}" if raw_url.startswith("/") else raw_url
            
            practice = data.get("practice", {})
            
            lat = practice.get("latitude")
            lon = practice.get("longitude")
            if not lat or not lon:
                lat = data.get("locality_latitude")
                lon = data.get("locality_longitude")

            try:
                lat = float(lat) if lat else None
                lon = float(lon) if lon else None
            except (ValueError, TypeError):
                lat = None
                lon = None

            doc = {
                "ID": data.get("id"),
                "Name": data.get("doctor_name"),
                "Specialization": data.get("specialization"),
                "Experience": data.get("experience_years", 0),
                "Rating": data.get("recommendation_percent", 0),
                "Reviews": data.get("reviews_count", 0),
                "Fees": data.get("consultation_fees", 0),
                "Hospital": practice.get("name", "Clinic"),
                "Locality": practice.get("locality", ""),
                "lat": lat, 
                "lon": lon,
                "Image": data.get("profile_photo", {}).get("url", ""),
                "Profile_Link": full_url,
                "Keyword_Used": search_term
            }
            if doc["Rating"] is None: doc["Rating"] = 0
            doctors_list.append(doc)
    except AttributeError:
        pass
    return doctors_list

# --- 4. AGGREGATOR ---
def get_all_results(city, main_kw, related_kws, max_pages=5):
    all_data = []
    keywords = [main_kw] + [k.strip() for k in related_kws.split(',') if k.strip()]
    
    progress_bar = st.progress(0)
    status_txt = st.empty()
    total_ops = len(keywords) * max_pages
    completed_ops = 0
    
    for kw in keywords:
        for page in range(1, max_pages + 1):
            status_txt.text(f"Searching for '{kw}' in {city} (Page {page})...")
            data = fetch_data(city, kw, page)
            if data:
                parsed = parse_doctors(data, kw)
                all_data.extend(parsed)
            completed_ops += 1
            progress_bar.progress(min(completed_ops / total_ops, 1.0))
            time.sleep(0.3)
            
    progress_bar.empty()
    status_txt.empty()
    
    df = pd.DataFrame(all_data)
    if not df.empty:
        df = df.drop_duplicates(subset=["ID"])
    return df

# --- 5. STREAMLIT UI ---
st.set_page_config(page_title="Doctor Finder", layout="wide")

st.markdown("""
<style>
    .doctor-card { background-color: var(--secondary-background-color); color: var(--text-color); padding: 20px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 20px; }
    .optimal-card { border: 2px solid #28a745; background-color: rgba(40, 167, 69, 0.08); }
    .label { font-size: 0.8em; opacity: 0.7; text-transform: uppercase; }
    .sub-text { font-size: 0.95em; opacity: 0.9; line-height: 1.4; }
    .book-btn { display: inline-block; padding: 8px 16px; background-color: #007bff; color: white !important; text-decoration: none; border-radius: 6px; font-size: 0.9em; font-weight: bold; text-align: center; }
    .book-btn:hover { background-color: #0056b3; }
    .profile-img { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid var(--background-color); box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .price-tag { font-weight: bold; font-size: 1.3em; color: var(--text-color); margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Search Parameters")
    city_input = st.text_input("City")
    main_kw_input = st.text_input("Primary Condition")
    related_kw_input = st.text_area("Related Keywords")
    
    # 5 pages default hardcoded
    pages_to_scrape = 6  
    st.caption(f"Deep Search Enabled")

    if 'data' not in st.session_state:
        st.session_state.data = pd.DataFrame()

    search_btn = st.button("Find Doctors", type="primary")

st.title(f"Doctor Search: {city_input}")

if search_btn and main_kw_input:
    df = get_all_results(city_input, main_kw_input, related_kw_input, pages_to_scrape)
    st.session_state.data = df

if not st.session_state.data.empty:
    df = st.session_state.data
    
    st.sidebar.divider()
    st.sidebar.header("Filter Results")
    
    # Dynamic Filters
    max_price = int(df['Fees'].max()) if not df['Fees'].empty else 2000
    min_price = int(df['Fees'].min()) if not df['Fees'].empty else 0
    price_filter = st.sidebar.slider("Max Consultation Fee", min_price, max_price, max_price, step=100)
    
    max_exp = int(df['Experience'].max()) if not df['Experience'].empty else 20
    exp_filter = st.sidebar.slider("Minimum Experience (Years)", 0, max_exp, 0)
    
    rating_filter = st.sidebar.slider("Minimum Satisfaction (%)", 0, 100, 0)

    # 1. Apply Filters
    filtered_df = df[
        (df['Fees'] <= price_filter) & 
        (df['Experience'] >= exp_filter) &
        (df['Rating'] >= rating_filter)
    ].copy()
    
    # 2. CALCULATE WEIGHTED SCORE (The "Best Doctor" Logic)
    # Formula: Rating (0-100) + (Experience * 1.5) + (SquareRoot(Reviews) * 5)
    # This prioritizes high experience and high reviews significantly over simple high rating
    filtered_df['Score'] = (
        filtered_df['Rating'] + 
        (filtered_df['Experience'] * 1.5) + 
        (filtered_df['Reviews'] ** 0.5 * 5)
    )

    # 3. Sort by Score (Price is ignored in sorting, so quality wins)
    sorted_df = filtered_df.sort_values(by="Score", ascending=False).reset_index(drop=True)

    tab1, tab2 = st.tabs(["List View", "Map View"])

    with tab1:
        if not sorted_df.empty:
            st.caption(f"Showing {len(sorted_df)} doctors matching filters")
            
            top_doc = sorted_df.iloc[0]
            st.subheader("Top Pick Match")
            
            # Use Textwrap to ensure clean HTML rendering
            html_top = create_doctor_card(
                top_doc['Name'], top_doc['Specialization'], top_doc['Hospital'], 
                top_doc['Locality'], top_doc['Rating'], top_doc['Reviews'], 
                top_doc['Experience'], top_doc['Fees'], top_doc['Image'], 
                top_doc['Profile_Link'], is_optimal=True
            )
            st.markdown(html_top, unsafe_allow_html=True)
            st.divider()
            
            for i, row in sorted_df.iloc[1:].iterrows():
                html_card = create_doctor_card(
                    row['Name'], row['Specialization'], row['Hospital'], 
                    row['Locality'], row['Rating'], row['Reviews'], 
                    row['Experience'], row['Fees'], row['Image'], 
                    row['Profile_Link'], is_optimal=False
                )
                st.markdown(html_card, unsafe_allow_html=True)
        else:
            st.warning("No doctors match your specific filters.")

    with tab2:
        map_df = sorted_df.copy()
        map_df['lat'] = pd.to_numeric(map_df['lat'], errors='coerce')
        map_df['lon'] = pd.to_numeric(map_df['lon'], errors='coerce')
        map_df = map_df.dropna(subset=['lat', 'lon'])
        
        if not map_df.empty:
            st.success(f"Plotting locations for {len(map_df)} doctors.")
            
            # Jittering logic
            map_df['lat'] = map_df['lat'] + np.random.normal(0, 0.0002, size=len(map_df))
            map_df['lon'] = map_df['lon'] + np.random.normal(0, 0.0002, size=len(map_df))

            view_state = pdk.ViewState(
                latitude=map_df["lat"].mean(),
                longitude=map_df["lon"].mean(),
                zoom=11, pitch=0,
            )

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=60, 
                pickable=True,
                auto_highlight=True,
            )

            tooltip = {
                "html": """
                    <div style="background-color: white; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: black; min-width: 150px;">
                        <b style="font-size: 14px;">{Name}</b><br/>
                        <span style="color: grey; font-size: 12px;">{Hospital}</span><br/>
                        <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;"/>
                        Fees: <b>₹{Fees}</b> <br/>
                        Rating: <b>{Rating}%</b><br/>
                        Exp: <b>{Experience} Yrs</b>
                    </div>
                """,
                "style": {"color": "black"}
            }

            st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=view_state, layers=[layer], tooltip=tooltip))

            # st.markdown("#### 📍 Location Details")
            # st.dataframe(map_df[['Name', 'Hospital', 'Locality', 'Fees']], use_container_width=True, hide_index=True)
        else:
            st.error("⚠️ No coordinates found in API.")

elif search_btn:
    st.warning("No doctors found.")