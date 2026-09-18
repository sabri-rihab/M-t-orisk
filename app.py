import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Météorisk Dashboard", layout="wide")

st.title("Météorisk : Moroccan Weather Risk Dashboard")


# docker exec -it meteorisk_airflow_webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@meteorisk.com --password admin

# Get database connection string from environment
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:2004@postgres:5432/meteorisk")

@st.cache_data(ttl=300)
def load_weather_data():
    engine = create_engine(db_url)
    query = """
        SELECT 
            c.name AS city,
            ar.name AS region,
            c.lat,
            c.lng,
            wd.forecast_date,
            wd.temperature_2m_max,
            wd.temperature_2m_min,
            wd.precipitation_sum,
            wd.wind_speed_10m_max,
            wd.temp_category,
            wd.rain_category,
            wd.wind_category,
            wd.risk_score
        FROM weather_detail wd
        JOIN city c ON wd.city_id = c.id
        JOIN admin_region ar ON c.admin_id = ar.id
        ORDER BY wd.forecast_date ASC
    """
    return pd.read_sql(query, con=engine)

try:
    df = load_weather_data()

    # Sidebar Filter
    st.sidebar.header("Filters")
    regions = ["All Regions"] + sorted(df["region"].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("Select Region", regions)

    if selected_region != "All Regions":
        df = df[df["region"] == selected_region]

    # Top Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tracked Cities", df["city"].nunique())
    col2.metric("Highest Risk Score", f"{df['risk_score'].max():.1f}")
    col3.metric("Max Temperature", f"{df['temperature_2m_max'].max()} °C")
    col4.metric("Max Wind Speed", f"{df['wind_speed_10m_max'].max()} km/h")

    # Map View
    st.subheader("📍 City Map Locations")
    st.map(df[["lat", "lng"]].rename(columns={"lng": "lon"}))

    # High Risk Alerts Section
    st.subheader("⚠️ High Weather Risks (Score > 20)")
    high_risk_df = df[df["risk_score"] > 20]
    if not high_risk_df.empty:
        st.dataframe(high_risk_df[["city", "region", "forecast_date", "risk_score", "temp_category", "wind_category", "rain_category"]], use_container_width=True)
    else:
        st.info("No extreme weather risks detected.")

    # Data Table
    st.subheader("📊 Detailed Weather Records")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Unable to connect to database: {e}")