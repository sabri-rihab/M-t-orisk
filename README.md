```
# 🌤️ Météorisk — End-to-End Weather Risk ETL Pipeline &amp; Dashboard

## 📋 Project Overview
**Météorisk** is a decision-support data engineering system designed for a delivery logistics company operating across Moroccan cities. The system fetches multi-day weather forecasts, cleans and normalizes raw data, engineers categorical hazards and a composite **Weather Risk Score (0–100)**, loads the structured data into PostgreSQL, and presents interactive insights via a **Streamlit Dashboard** automated by **Apache Airflow** and **Docker**.

---

## 🏗️ Architecture (Medallion Pattern)

```

[Open-Meteo API &amp; ma.csv] │ ▼ [Bronze Layer] ──&gt; Raw JSON payloads (Bronz/bronze\_data.csv) │ ▼ [Silver Layer] ──&gt; Exploded, deduplicated, interpolated records (Silver/silver\_data.csv) │ ▼ [Gold Layer] ──&gt; Feature engineering &amp; Risk Score (Gold/gold\_data.csv) │ ▼ [PostgreSQL] ──&gt; Relational DB (admin\_region, city, weather\_detail) │ ┌─────┴──────────────┐ │ │ ▼ ▼ [SQL Analysis] [Streamlit Dashboard]

```

---

## 🚀 Step-by-Step Breakdown

### Étape 1: Data Extraction (Bronze Layer)
* **Goal**: Fetch multi-day daily weather forecasts for Moroccan cities while preserving raw API responses [cite: 8, 9].
* **Source Inputs**: `ma.csv` containing city names, administrative regions, latitudes, and longitudes [cite: 7].
* **API Target**: Open-Meteo Forecast API (`temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `precipitation_probability_max`, `wind_speed_10m_max`, `wind_gusts_10m_max`, `weather_code`) [cite: 8].
* **Resilience**: Implements `try/except` blocks and timeout configurations (`timeout=10`) so individual city failures do not crash the batch job [cite: 9, 18].
* **Storage**: Output saved as `Bronz/bronze_data.csv` [cite: 9].

### Étape 2: Cleaning &amp; Standardization (Silver Layer)
* **Goal**: Transform unnested daily JSON arrays into an atomic, relational 1-row-per-city-per-date grain [cite: 9, 16].
* **Key Operations**:
  1. Parses daily string dictionaries using `ast.literal_eval` and flattens them via `pd.json_normalize` [cite: 19].
  2. Unnests list columns using `explode()` [cite: 16, 19].
  3. Standardizes column names (`time` → `forecast_date`) and formats dates (`YYYY-MM-DD`) [cite: 19, 22].
  4. Imputes missing dates per city using forward fill (`ffill`) and time offsets [cite: 61, 305].
  5. Interpolates missing numerical values per city using linear mean interpolation (`interpolate(method='linear')`) with boundary fill (`ffill().bfill()`) [cite: 61, 305].
  6. Removes duplicate records based on the business key `(city, forecast_date)` [cite: 19, 30].
* **Storage**: Saved as `Silver/silver_data.csv` [cite: 10, 19].

### Étape 3: Feature Engineering, Scoring &amp; Database Load (Gold Layer)
* **Goal**: Compute operational hazard categories, derive the 0–100 Weather Risk Score, and load data into PostgreSQL [cite: 10, 11].
* **Engineered Features**:
  * `temp_category`: Binned into 9 levels ('Extreme Freezing' to 'Extreme Hot') [cite: 4, 65].
  * `rain_category`: Binned into 5 levels ('Dry' to 'Extreme Rain') [cite: 4, 63].
  * `wind_category`: Binned into 5 levels ('Calm' to 'Severe Storm') [cite: 4, 63].
  * `risk_score`: Weighted composite score (37.5% Rain + 37.5% Wind + 25% Temp deviation) [cite: 96, 289].
* **Database Schema**:
  * `admin_region` (Parent dimension: `id`, `name`) [cite: 4, 291].
  * `city` (Child dimension: `id`, `name`, `lat`, `lng`, `admin_id`) [cite: 4, 291].
  * `weather_detail` (Fact table: foreign key `city_id`, `forecast_date`, metrics, categories, `risk_score`) [cite: 4, 292].
* **Deduplication / Upsert Strategy**: Clears existing records for matching `(city_id, forecast_date)` pairs prior to insertion to handle pipeline re-runs gracefully [cite: 11, 279].

### Étape 4: Business SQL Analytics
* **Goal**: Query PostgreSQL to answer key operational questions [cite: 11, 12]:
  1. Top 5 hottest cities by max temperature [cite: 12, 303].
  2. Top 5 rainiest cities by total rainfall [cite: 12, 303].
  3. Top 5 highest risk cities by average risk score [cite: 12, 303].
  4. Top 5 dates with maximum risk scores [cite: 12, 303].
  5. Peak risk forecast date for each city [cite: 12, 303].

### Étape 5: Interactive Decision-Support Dashboard
* **Goal**: Provide operational managers with a UI to monitor weather risks and adapt delivery schedules [cite: 8, 12, 13].
* **Components**:
  * **Top KPIs**: Total cities, highest risk score, max temp, max rain [cite: 12, 277].
  * **Interactive Map**: Geographical plotting of Moroccan city locations [cite: 277].
  * **High-Risk Alerts**: Color-coded table highlighting instances where `risk_score &gt; 20` [cite: 277].
  * **Top 5 Insights**: Visual Plotly bar charts answering Étape 4 questions [cite: 283].
  * **Interactive Trend Charts**: Plotly line chart with city/factor selectboxes, week vs. day toggles, Y-axis zooming, and unified hover tooltips [cite: 277].
  * **Sidebar Filters**: Filter entire dashboard by region and minimum risk score slider [cite: 277, 281].

### Étape 6: Orchestration &amp; Docker Infrastructure
* **Goal**: Automate execution schedules and containerize all services [cite: 13, 14].
* **Airflow DAG (`meteorisk_etl_pipeline`)**:
  * Scheduled `@daily` with retry policies (`retries=2`, `retry_delay=5 min`) [cite: 13, 302].
  * Tasks: `extract_task` ➔ `transform_task` ➔ `load_task` using `@task` decorators [cite: 302].
* **Docker Compose Services**:
  * `postgres`: PostgreSQL database instance [cite: 165, 201].
  * `airflow-webserver`: Airflow UI &amp; Scheduler running in standalone mode [cite: 165, 201].
  * `streamlit`: Streamlit dashboard web server [cite: 165, 201].

---

## 🛠️ Complete Predefined &amp; Custom Function Reference

### 1. Extraction Module (`extract.py`)
| Function | Parameters | Description |
| :--- | :--- | :--- |
| `extract()` | None | Reads `ma.csv`, queries Open-Meteo API for each city's forecast with error handling, attaches metadata, and exports raw data to `Bronz/bronze_data.csv` [cite: 308]. |

---

### 2. Transformation Module (`transform.py`)
| Function | Parameters | Description |
| :--- | :--- | :--- |
| `transform()` | None | Reads Bronze data, un-nests JSON structures, explodes array columns into daily rows, imputes missing dates/metrics, deduplicates rows, and saves `Silver/silver_data.csv` [cite: 305]. |
| `validate_data_quality(df)` | `df` (DataFrame) | Asserts data boundaries (temp between -20°C and 60°C, non-negative rain/wind, no null forecast dates) [cite: 285]. |

---

### 3. Feature Engineering &amp; Load Module (`load.py`)
| Function | Parameters | Description |
| :--- | :--- | :--- |
| `get_temp_category(temp)` | `temp` (float) | Assigns one of 9 temperature categories ('Extreme Freezing' to 'Extreme Hot') based on temperature thresholds [cite: 287]. |
| `get_rain_category(rain)` | `rain` (float) | Assigns one of 5 rainfall categories ('Dry' to 'Extreme Rain') based on daily mm thresholds [cite: 288]. |
| `get_wind_category(wind)` | `wind` (float) | Assigns one of 5 wind categories ('Calm' to 'Severe Storm') based on km/h thresholds [cite: 288]. |
| `calculate_risk_score(rain_mm, wind_kmh, temp_max, temp_min)` | `rain_mm`, `wind_kmh`, `temp_max`, `temp_min` | Calculates the composite 0–100 Weather Risk Score using weighted sub-scores (37.5% Rain, 37.5% Wind, 25% Temp deviation) [cite: 289]. |
| `transform_silver_to_gold(df)` | `df` (DataFrame) | Applies categorization functions and risk score calculation across the Silver DataFrame and outputs `Gold/gold_data.csv` [cite: 293]. |
| `load_to_postgres(df_gold, db_url)` | `df_gold` (DataFrame), `db_url` (str) | Sets up SQLAlchemy ORM tables (`AdminRegion`, `City`, `WeatherDetail`), handles foreign key mapping, executes duplicate deletion, and bulk-inserts records into PostgreSQL [cite: 279, 294]. |

---

### 4. Dashboard Module (`app.py`)
| Function | Parameters | Description |
| :--- | :--- | :--- |
| `load_weather_data()` | None | Cached function (`ttl=300`) executing SQL JOINs across `weather_detail`, `city`, and `admin_region` to return a unified DataFrame [cite: 298]. |
| `apply_risk_color(val)` | `val` (float) | Returns CSS string for background colors (&gt;50 red, &gt;20 orange, ≤20 green) to style risk table rows [cite: 300]. |

---

### 5. Orchestration Module (`dags/weather_dag.py`)
| Function / Task | Parameters | Description |
| :--- | :--- | :--- |
| `extract_task()` | None | Airflow `@task` wrapper triggering `extract()` [cite: 302]. |
| `transform_task()` | None | Airflow `@task` wrapper triggering `transform()` [cite: 302]. |
| `load_task()` | None | Airflow `@task` wrapper reading `Silver/silver_data.csv`, running `transform_silver_to_gold()`, and invoking `load_to_postgres()` [cite: 302]. |

---

## 🧮 Business Risk Score Justification

\[\text{Risk Score} = \left( 0.375 \times \text{Rain Risk} + 0.375 \times \text{Wind Risk} + 0.25 \times \text{Temp Risk} \right) \times 100\]

1. **Rain Sub-Score (37.5% Weight)**: Scaled linearly up to 50 mm/day [cite: 289]. Rain poses immediate traction, hydroplaning, and package damage hazards during delivery handoffs [cite: 83, 94].
2. **Wind Sub-Score (37.5% Weight)**: Scaled linearly up to 75 km/h (Beaufort Gale force) [cite: 83, 289]. Wind destabilizes two-wheeler balance and creates lateral hazards [cite: 83, 94].
3. **Temperature Sub-Score (25% Weight)**: Measures deviation from the 21.5°C human optimal comfort midpoint [cite: 108, 289]. Extreme heat (&gt;40°C) or freezing (&lt;0°C) induces driver fatigue and thermal stress [cite: 83, 110].
```