import os
import pandas as pd
from sqlalchemy import create_engine

# 1. Connect to PostgreSQL (uses 'postgres' host for Docker container networking)
default_host = "localhost" if os.name == "nt" else "postgres"
db_url = os.getenv("DATABASE_URL", f"postgresql://postgres:2004@{default_host}:5432/meteorisk")
engine = create_engine(db_url)

# 2. Define the 5 Business SQL Queries
queries = {
    "1. Top 5 Cities with Highest Maximum Temperature": """
        SELECT c.name AS city, MAX(wd.temperature_2m_max) AS max_temp 
        FROM weather_detail wd 
        JOIN city c ON wd.city_id = c.id 
        GROUP BY c.name 
        ORDER BY max_temp DESC 
        LIMIT 5;
    """,
    "2. Top 5 Cities with Highest Total Precipitation": """
        SELECT c.name AS city, SUM(wd.precipitation_sum) AS total_rain 
        FROM weather_detail wd 
        JOIN city c ON wd.city_id = c.id 
        GROUP BY c.name 
        ORDER BY total_rain DESC 
        LIMIT 5;
    """,
    "3. Top 5 Cities with Highest Average Risk Score": """
        SELECT c.name AS city, ROUND(AVG(wd.risk_score)::numeric, 2) AS avg_risk 
        FROM weather_detail wd 
        JOIN city c ON wd.city_id = c.id 
        GROUP BY c.name 
        ORDER BY avg_risk DESC 
        LIMIT 5;
    """,
    "4. Top 5 Dates with Maximum Risk Score": """
        SELECT wd.forecast_date, ROUND(MAX(wd.risk_score)::numeric, 2) AS max_risk 
        FROM weather_detail wd 
        GROUP BY wd.forecast_date 
        ORDER BY max_risk DESC 
        LIMIT 5;
    """,
    "5. Highest Risk Period per City": """
        SELECT DISTINCT ON (c.name) c.name AS city, wd.forecast_date, wd.risk_score 
        FROM weather_detail wd 
        JOIN city c ON wd.city_id = c.id 
        ORDER BY c.name, wd.risk_score DESC;
    """
}

# 3. Execute and Print Results
for title, sql in queries.items():
    print("\n==========================================")
    print(f" {title} ")
    print("==========================================")
    df = pd.read_sql(sql, engine)
    print(df.to_string(index=False))