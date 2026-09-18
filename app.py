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
    # it support specific keys : ex : "Get help", "Report a bug"
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
    """Fetch weather records joined with city and administrative region metadata from PostgreSQL."""
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
    min_risk = st.sidebar.slider("Minimum Risk Score Filter", 0, 100, 0)
    df = df[df["risk_score"] >= min_risk]


    # -------------------------------------------------------------------------
    # 4. KEY BUSINESS METRICS (KPIs from Context Brief)
    # -------------------------------------------------------------------------
    # Displays top business indicators required by operational managers
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tracked Cities", df["city"].nunique())
    col2.metric("Highest Risk Score", f"{df['risk_score'].max():.1f}")
    col3.metric("Max Temperature", f"{df['temperature_2m_max'].max()} °C")
    col4.metric("Max Precipitation", f"{df['precipitation_sum'].max()} mm")

    st.divider()

    # -------------------------------------------------------------------------
    # 5. GEOGRAPHICAL MAP VISUALIZATION
    # -------------------------------------------------------------------------
    # Streamlit map requires longitude column to be explicitly named 'lon'
    st.subheader("📍 Moroccan Cities Weather Map")
    st.map(df[["lat", "lng"]].rename(columns={"lng": "lon"}))

    st.divider()

    # -------------------------------------------------------------------------
    # 6. HIGH RISK ALERTS SECTION (Score > 20)
    # -------------------------------------------------------------------------
    st.subheader("⚠️ High Weather Risk Alerts (Score > 20)")

    # Filter dataset for high-risk instances (risk_score > 20)
    high_risk_df = df[df["risk_score"] > 20][
        ["city", "region", "forecast_date", "risk_score", "temp_category", "wind_category", "rain_category"]
    ]

    if not high_risk_df.empty:

        # =====================================================================
        # CODE WITHOUT COLORS (COMMENTED OUT AS REQUESTED)
        # =====================================================================
        # Description: Standard dataframe display without visual background styling.
        # st.dataframe(high_risk_df, use_container_width=True)
        # =====================================================================

        # =====================================================================
        # CODE WITH COLORS & STYLING (ACTIVE CODE)
        # =====================================================================
        # Function to assign color badges depending on risk score level:
        # - Moderate Risk (20 - 50): Soft Orange background
        # - High Risk (> 50): Soft Red background
        def apply_risk_color(val):
            """Returns CSS styling string based on risk score threshold."""
            if val > 50:
                return 'background-color: #ff4d4d; color: white; font-weight: bold;'  # Red for extreme risk
            elif val > 20:
                return 'background-color: #ffa64d; color: black; font-weight: bold;'  # Orange for moderate risk
            return 'background-color: #70db70; color: black;'                      # Green for low risk

        # Apply styling function to the 'risk_score' column and format decimal places
        styled_high_risk = high_risk_df.style.map(apply_risk_color, subset=['risk_score'])\
                                              .format({'risk_score': '{:.1f}'})

        # Render styled dataframe in Streamlit UI
        st.dataframe(styled_high_risk, use_container_width=True)
        # =====================================================================

    else:
        st.info("No extreme weather risks detected for the selected region.")

    st.divider()

    # -------------------------------------------------------------------------
    # 7. INTERACTIVE WEATHER TRENDS DIAGRAM (With Hover & Scaling)
    # -------------------------------------------------------------------------
    st.subheader("📈 Interactive Weather Trends & Forecasts")

    col_city, col_time, col_factor = st.columns(3)

    # City selection dropdown
    with col_city:
        selected_city = st.selectbox("Select City", options=sorted(df["city"].unique()))

    # Timeframe selector (Full 7-day week vs specific day)
    with col_time:
        timeframe = st.radio("Timeframe", options=["Full Week", "Specific Day"], horizontal=True)

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

    # Filter and order forecast data for selected city
    city_chart_df = df[df["city"] == selected_city].sort_values("forecast_date")

    # Filter for a specific date if selected
    if timeframe == "Specific Day":
        selected_date = st.selectbox("Select Specific Forecast Date", options=city_chart_df["forecast_date"].unique())
        city_chart_df = city_chart_df[city_chart_df["forecast_date"] == selected_date]

    # Calculate dynamic Y-axis bounds to zoom in on curve variations
    min_val = city_chart_df[selected_cols].min().min()
    max_val = city_chart_df[selected_cols].max().max()
    padding = 2 if min_val == max_val else (max_val - min_val) * 0.2

    # Build interactive Plotly line chart
    fig = px.line(
        city_chart_df,
        x="forecast_date",
        y=selected_cols,
        markers=True,
        labels={"forecast_date": "Date", "value": selected_label, "variable": "Metric"}
    )

    # Configure unified hover box showing values when hovering over the curves
    fig.update_layout(
        hovermode="x unified",               # Shows exact values for all active curves in one hover box
        template="plotly_white",             # Clean white background theme
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    # Set dynamic zoom range on Y-axis
    fig.update_yaxes(range=[min_val - padding, max_val + padding])

    # Display Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -------------------------------------------------------------------------
    # 7.5. TOP 5 BUSINESS RANKINGS (Étape 4 Insights)
    # -------------------------------------------------------------------------
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
            text_auto=".1f",
            labels={"city": "City", "temperature_2m_max": "Max Temp (°C)"},
            color="temperature_2m_max",
            color_continuous_scale="Reds",
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

    # -------------------------------------------------------------------------
    # 8. DETAILED WEATHER DATA RECORDS TABLE
    # -------------------------------------------------------------------------
    st.subheader("📊 Full Weather Database Records")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Unable to connect to database or render dashboard: {e}")