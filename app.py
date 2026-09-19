import os
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

# _____________________________________________________________________________
# Configuration page streamlit
st.set_page_config(
    page_title="Météorisk Dashboard",
    page_icon="🌤️",
    layout="wide",
    # layout="centered"
    # initial_sidebar_state="collapsed", # expended
    # menu_items support specific keys : ex : "Get help", "Report a bug"
    menu_items={
        "About": "Météorisk - Weather Risk Dashboard",
    }
)

st.title("🌤️ Météorisk : Moroccan Weather Risk Dashboard")
st.markdown("Decision-support system for monitoring meteorological hazards and adjusting logistics schedules across Morocco.")

#________________________________________________________________________________
# st.markdown("## test") #display formatted markdown/html
# st.markdown("<h1 style='color:red'>MétéoRisk</h1>", unsafe_allow_html=True)
# st.write("") #display everything + 
# st.write_stream(generate_text) # to display progressive content? 


# ________________________________________________________________________________
# DATABASE CONNECTION & DATA LOADING

# Fetch database connection string from Docker environment 
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
    # Load dataset from PostgreSQL
    df = load_weather_data()

    # _______________________________________________________
    # SIDEBAR  FILTERS
    st.sidebar.header("🔍 Filters")

    # ________________________
    # region filter
    regions = ["All Regions"] + sorted(df["region"].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("Select Administrative Region", regions)

    # Filter dataframe dynamically based on selected region
    if selected_region != "All Regions":
        df = df[df["region"] == selected_region]

    # ________________________
    # risk level slider
    min_risk = st.sidebar.slider("Minimum Risk Score Filter", 0, 100, 0) #label, min, max, valeur_initial, step
    df = df[df["risk_score"] >= min_risk]


    # _______________________________________________________________________
    # Displays top business indicators required by operational managers
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tracked Cities", df["city"].nunique())
    col2.metric("Highest Risk Score", f"{df['risk_score'].max():.1f}")
    col3.metric("Max Temperature", f"{df['temperature_2m_max'].max()} °C")
    col4.metric("Max Precipitation", f"{df['precipitation_sum'].max()} mm")
    col5.metric('hello', 15)

    st.divider()  

    #___________________________________________________________________________________
    # <___________ the MAP <(°_°)> ___________>
    st.subheader("📍 Moroccan Cities Weather Map")
    st.map(df, latitude= 'lat', longitude= 'lng', color="#d2e363")
    # st.map(df[["lat", "lng"]].rename(columns={"lng": "lon"})) # we can rename the column lng -> lan
    # parameters : data, *, latitude, longitude, color, size, zoom, use_container_width
    st.divider()

    # __________________________________________________________________________________
    # ___________________<( HIGH RISK ALERTS )>________________________
    st.subheader("⚠️ High Weather Risk Alerts (Score > 20)")
    high_risk_df = df[df["risk_score"] > 20][
        ["city", "region", "forecast_date", "risk_score", "temp_category", "wind_category", "rain_category"]
    ]

    if not high_risk_df.empty:
        # display without visual background styling
        high_risk_df = high_risk_df.sort_values("risk_score", ascending=False)
        # st.dataframe(high_risk_df, use_container_width=True)

        # with styling => color depend on the risk score
        def apply_risk_color(val):
            if val > 50:
                return 'background-color: #ff4d4d; color: white; font-weight: bold;'  # red for extreme risk
            elif val > 20:
                return 'background-color: #ffa64d; color: black; font-weight: bold;'  # orange for moderate risk
            return 'background-color: #70db70; color: black;'                      # green for low risk

        styled_high_risk = high_risk_df.style.map(apply_risk_color, subset=['risk_score'])
        st.dataframe(styled_high_risk, use_container_width=True)
        # =====================================================================

    else:
        st.info("No extreme weather risks detected for the selected region.")

    st.divider()

    #____________________________________________________________________________
    #__________________<( WEATHER DIAGRAM With Hover & Scaling )>________________
    st.subheader("📈 Interactive Weather Trends & Forecasts")

    col_city, col_factor = st.columns(2)

    # City selection dropdown
    with col_city:
        selected_city = st.selectbox("Select City", options=sorted(df["city"].unique()))

    # Weather factor selection mapping (Combines Min and Max temperature)
    with col_factor:
        factor_mapping = {
            "Temperature (°C)": ["temperature_2m_min", "temperature_2m_max"],
            "Precipitation (mm)": ["precipitation_sum"],
            "Wind Speed (km/h)": ["wind_speed_10m_max"],
            "Risk Score (0-100)": ["risk_score"],
        }
        selected_label = st.selectbox("Select Weather Factor", options=list(factor_mapping.keys()))

    selected_cols = factor_mapping[selected_label]

    # df for the selected city infos + sort the dates 
    city_chart_df = df[df["city"] == selected_city].sort_values("forecast_date")

    # The figure for temp/wind/precipitation
    figure = px.line(
        city_chart_df,
        x="forecast_date",
        y=selected_cols,
        markers=True, #shows the dotes/points
        labels={"forecast_date": "Date", "value": selected_label, "variable": "Metric"}
        # title = 'quelque chose',
        # hover_data=["forecast_date", "risk_score"], # shows additional infos when hovered
        # hover_name="city", # like a title to the showed infos 
    )

    # ______________<(3D)>___________________ 
    # figure = px.scatter_3d(
    #     city_chart_df,
    #     x="forecast_date",
    #     y="precipitation_sum",
    #     z='wind_speed_10m_max'
    # )
    st.plotly_chart(figure)
    st.divider()

    #___________________________________________________________________________
    # 7.5. TOP 5 BUSINESS RANKINGS (Étape 4 Insights)

    st.subheader("📊 Top 5 Operational Insights")
    tab_temp, tab_rain, tab_risk = st.tabs(
        ["🔥 Top Hottest Cities", "🌧️ Top Rainiest Cities", "⚠️ Highest Risk Cities"]
    )

    with tab_temp:
        top_temp_df = df.groupby("city")["temperature_2m_max"].max().reset_index()
        top_temp_df = top_temp_df.sort_values("temperature_2m_max", ascending=False).head(5)
        fig_temp = px.bar(
            top_temp_df,
            x="city",
            y="temperature_2m_max",
            text_auto=".1f", #put the value as text
            labels={"temperature_2m_max": "Max Temp (°C)"},
            color="temperature_2m_max",
            color_continuous_scale="reds",
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with tab_rain:
        top_rain_df = df.groupby("city")["precipitation_sum"].sum().reset_index()
        top_rain_df = top_rain_df.sort_values("precipitation_sum", ascending=False).head(5)
        fig_rain = px.bar(
            top_rain_df,
            x="city",
            y="precipitation_sum",
            text_auto=".1f",
            labels={"city": "City", "precipitation_sum": "Total Rain (mm)"},
            color="precipitation_sum",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_rain, use_container_width=True)

    with tab_risk:
        top_risk_df = df.groupby("city")["risk_score"].mean().reset_index()
        top_risk_df = top_risk_df.sort_values("risk_score", ascending=False).head(5)
        fig_risk = px.bar(
            top_risk_df,
            x="city",
            y="risk_score",
            text_auto=".1f",
            labels={"city": "City", "risk_score": "Average Risk Score"},
            color="risk_score",
            color_continuous_scale="Oranges",
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    # ______________________________________________________________
    # all weather data
    st.subheader("📊 Full Weather Database Records")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Unable to connect to database or render dashboard: {e}")