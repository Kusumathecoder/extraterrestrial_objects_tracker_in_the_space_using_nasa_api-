import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Asteroid Data Dashboard", layout="wide")

st.title("🌠 Asteroid Insights Dashboard")
st.markdown("Static + Real-Time NASA Asteroid Data Visualized")

# Load static data
@st.cache_data
def load_static_data():
    df = pd.read_csv('static_asteroids_data.csv')
    df['relative_velocity_kmph'] = pd.to_numeric(df['relative_velocity_kmph'], errors='coerce')
    df['miss_distance_km'] = pd.to_numeric(df['miss_distance_km'], errors='coerce')
    df['estimated_diameter_min_km'] = pd.to_numeric(df['estimated_diameter_min_km'], errors='coerce')
    df['estimated_diameter_max_km'] = pd.to_numeric(df['estimated_diameter_max_km'], errors='coerce')
    return df

# Load dynamic API data
@st.cache_data
def fetch_nasa_data():
    API_KEY = ''
    today = pd.Timestamp.today().strftime('%Y-%m-%d')
    url = f'https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={API_KEY}'
    response = requests.get(url)
    api_data = response.json()
    neos = []
    for date in api_data['near_earth_objects']:
        for obj in api_data['near_earth_objects'][date]:
            est_dia = obj['estimated_diameter']['kilometers']
            rel_vel = obj['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']
            miss_dist = obj['close_approach_data'][0]['miss_distance']['kilometers']
            neos.append({
                'id': obj['id'],
                'name': obj['name'],
                'absolute_magnitude_h': obj['absolute_magnitude_h'],
                'estimated_diameter_min_km': est_dia['estimated_diameter_min'],
                'estimated_diameter_max_km': est_dia['estimated_diameter_max'],
                'is_potentially_hazardous_asteroid': obj['is_potentially_hazardous_asteroid'],
                'close_approach_date': obj['close_approach_data'][0]['close_approach_date'],
                'relative_velocity_kmph': float(rel_vel),
                'miss_distance_km': float(miss_dist),
                'orbiting_body': obj['close_approach_data'][0]['orbiting_body']
            })
    return pd.DataFrame(neos)

# Load & combine
static_df = load_static_data()
dynamic_df = fetch_nasa_data()
combined_df = pd.concat([static_df, dynamic_df], ignore_index=True)

# Sidebar
st.sidebar.header("🔍 Filter Options")
hazard_filter = st.sidebar.selectbox("Show only hazardous asteroids?", options=["All", "Yes", "No"])
if hazard_filter == "Yes":
    combined_df = combined_df[combined_df['is_potentially_hazardous_asteroid'] == True]
elif hazard_filter == "No":
    combined_df = combined_df[combined_df['is_potentially_hazardous_asteroid'] == False]

st.markdown("### 📊 Visualizations")

# Visualization 1: Diameter vs Velocity
fig1 = px.scatter(
    combined_df,
    x="estimated_diameter_max_km",
    y="relative_velocity_kmph",
    color="is_potentially_hazardous_asteroid",
    labels={
        "estimated_diameter_max_km": "Max Estimated Diameter (km)",
        "relative_velocity_kmph": "Relative Velocity (km/h)",
        "is_potentially_hazardous_asteroid": "Hazardous?"
    },
    title="Estimated Diameter vs Relative Velocity",
)
st.plotly_chart(fig1, use_container_width=True)

# Visualization 2: Count by Orbiting Body
orbit_counts = combined_df['orbiting_body'].value_counts().reset_index()
orbit_counts.columns = ['orbiting_body', 'count']

fig2 = px.bar(
    orbit_counts,
    x='orbiting_body', y='count',
    labels={'orbiting_body': 'Orbiting Body', 'count': 'Asteroid Count'},
    color='orbiting_body',
    title='Asteroid Count by Orbiting Body'
)
st.plotly_chart(fig2, use_container_width=True)

# Visualization 3: Diameter Range Histogram
fig3 = px.histogram(
    combined_df,
    x='estimated_diameter_max_km',
    nbins=40,
    title='Distribution of Max Estimated Diameter (km)',
    labels={'estimated_diameter_max_km': 'Max Estimated Diameter (km)'},
    color='is_potentially_hazardous_asteroid'
)
st.plotly_chart(fig3, use_container_width=True)

# Visualization 4: Miss Distance vs Velocity
fig4 = px.scatter(
    combined_df,
    x='miss_distance_km',
    y='relative_velocity_kmph',
    color='is_potentially_hazardous_asteroid',
    title="Miss Distance vs Velocity",
    labels={
        "miss_distance_km": "Miss Distance (km)",
        "relative_velocity_kmph": "Relative Velocity (km/h)"
    }
)
st.plotly_chart(fig4, use_container_width=True)

# Data Table
st.markdown("### 📋 Combined Asteroid Data")
st.dataframe(combined_df)

# Option to download
csv = combined_df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", data=csv, file_name="combined_asteroid_data.csv", mime='text/csv')
