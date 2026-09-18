from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os
import pandas as pd

 
Base = declarative_base()



# ______________________________________________
def get_temp_category(temp):
    if temp < -15: return 'Extreme Freezing'
    elif temp < -5: return 'Very Freezing'
    elif temp < 0: return 'Freezing'
    elif temp < 10: return 'Very Cold'
    elif temp < 18: return 'Cold'
    elif temp < 25: return 'Moderate'
    elif temp < 32: return 'Hot'
    elif temp < 40: return 'Very Hot'
    else: return 'Extreme Hot'

# ______________________________________________
def get_rain_category(rain):
    if rain == 0: return 'Dry'
    elif rain <= 2.5: return 'Light Rain'
    elif rain <= 10: return 'Moderate Rain'
    elif rain <= 50: return 'Heavy Rain'
    else: return 'Extreme Rain'


# ______________________________________________
def get_wind_category(wind):
    if wind < 10: return 'Calm'
    elif wind <= 30: return 'Breezy'
    elif wind <= 50: return 'Strong Wind'
    elif wind <= 75: return 'Gale'
    else: return 'Severe Storm'


# ______________________________________________
#calculate the score_risk :
def calculate_risk_score(rain_mm, wind_kmh, temp_max, temp_min):
    # from 50mm is considered very dangerous
    rain_risk = min(rain_mm / 50.0, 1.0)
    
    # # from 75km/h is considered very dangerous
    wind_risk = min(wind_kmh / 75.0, 1.0)
    
    # 21.5C° is the perfect Temp. +20C° or -20C° from 21.5C° is considered dangerous/uncofortable
    temp_dev = max(abs(temp_max - 21.5), abs(temp_min - 21.5))
    temp_risk = min(temp_dev / 20.0, 1.0)
    
    # 37.5% Rain, 37.5% Wind, 25% Temp 
    score = (0.375 * rain_risk + 0.375 * wind_risk + 0.25 * temp_risk) * 100
    return round(score, 2)


# ______________________________________________
# postgres ENUM : 
TEMP_CATEGORIES = (
    'Extreme Freezing', # < -15°C
    'Very Freezing',    # -15°C to -5°C
    'Freezing',         # -5°C to 0°C
    'Very Cold',        # 0°C to 10°C
    'Cold',             # 10°C to 18°C
    'Moderate',         # 18°C to 25°C
    'Hot',              # 25°C to 32°C
    'Very Hot',         # 32°C to 40°C
    'Extreme Hot'       # > 40°C
)

RAIN_CATEGORIES = ('Dry', 'Light Rain', 'Moderate Rain', 'Heavy Rain', 'Extreme Rain')
WIND_CATEGORIES = ('Calm', 'Breezy', 'Strong Wind', 'Gale', 'Severe Storm')


# ______________________________________________
class AdminRegion(Base):
    __tablename__ = 'admin_region'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    cities = relationship("City", back_populates="admin_region")


class City(Base):
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    admin_id = Column(Integer, ForeignKey('admin_region.id'), nullable=False)

    admin_region = relationship("AdminRegion", back_populates="cities")
    weather_details = relationship("WeatherDetail", back_populates="city")


class WeatherDetail(Base):
    __tablename__ = 'weather_detail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, ForeignKey('city.id'), nullable=False)
    forecast_date = Column(Date, nullable=False)
    
    # Raw Weather Metrics
    temperature_2m_max = Column(Float)
    temperature_2m_min = Column(Float)
    precipitation_sum = Column(Float)
    precipitation_probability_max = Column(Float)
    wind_speed_10m_max = Column(Float)
    wind_gusts_10m_max = Column(Float)
    weather_code = Column(Integer)
    
    # Gold Features
    temp_category = Column(Enum(*TEMP_CATEGORIES, name="temp_enum"))
    rain_category = Column(Enum(*RAIN_CATEGORIES, name="rain_enum"))
    wind_category = Column(Enum(*WIND_CATEGORIES, name="wind_enum"))
    risk_score = Column(Float)

    city = relationship("City", back_populates="weather_details")



# _________________________________________________
def transform_silver_to_gold(df: pd.DataFrame) -> pd.DataFrame:
    #  copying the silver df
    df_gold = df.copy()

    # adding the categories column to the gold df
    df_gold['temp_category'] = df_gold['temperature_2m_max'].apply(get_temp_category)
    df_gold['rain_category'] = df_gold['precipitation_sum'].apply(get_rain_category)
    df_gold['wind_category'] = df_gold['wind_speed_10m_max'].apply(get_wind_category)

    # adding the risk_score column
    df_gold['risk_score'] = df_gold.apply(
        lambda row: calculate_risk_score(
            rain_mm=row['precipitation_sum'],
            wind_kmh=row['wind_speed_10m_max'],
            temp_max=row['temperature_2m_max'],
            temp_min=row['temperature_2m_min']
        ),
        axis=1
    )
    df_gold.to_csv('Gold/gold_data.csv', index=False)
    return df_gold

# silver = pd.read_csv('Silver/silver_data.csv')
# transform_silver_to_gold(silver)



# ___________________________
# insert the df_gold data into the db tables:
def load_to_postgres(df_gold: pd.DataFrame, db_url: str):
    engine = create_engine(db_url)
    
    # Create tables if they do not exist
    Base.metadata.create_all(engine)
    
    # Stream directly to PostgreSQL with ENUM handling
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 2. Populate Admin Regions
        unique_regions = df_gold['admin_name'].dropna().unique()
        for region in unique_regions:
            if not session.query(AdminRegion).filter_by(name=region).first():
                session.add(AdminRegion(name=region))
        session.commit()

        # 3. Populate Cities
        unique_cities = df_gold[['city', 'lat', 'lng', 'admin_name']].drop_duplicates()
        for _, row in unique_cities.iterrows():
            if not session.query(City).filter_by(name=row['city']).first():
                admin = session.query(AdminRegion).filter_by(name=row['admin_name']).first()
                session.add(City(
                    name=row['city'], 
                    lat=row['lat'], 
                    lng=row['lng'], 
                    admin_id=admin.id
                ))
        session.commit()

        # 4. Map the new city_ids back to the dataframe
        db_cities = session.query(City).all()
        city_id_map = {c.name: c.id for c in db_cities}
        df_gold['city_id'] = df_gold['city'].map(city_id_map)

        # 5. Filter the dataframe to ONLY include weather_detail columns
        # Ensure we drop any rows that failed to map a city_id
        df_weather = df_gold.dropna(subset=['city_id']).copy()

        # 5. Filter the dataframe to ONLY include weather_detail columns
        weather_cols = [
            'city_id', 'forecast_date', 'temperature_2m_max', 'temperature_2m_min', 
            'precipitation_sum', 'precipitation_probability_max', 'wind_speed_10m_max', 
            'wind_gusts_10m_max', 'weather_code', 'temp_category', 'rain_category', 
            'wind_category', 'risk_score'
        ]
        df_weather = df_gold[weather_cols]

        # 6. Insert into weather_detail
        df_weather.to_sql(
            'weather_detail', 
            con=engine, 
            if_exists='append', 
            index=False
            # dtype={
            #     'temp_category': Enum(*TEMP_CATEGORIES, name="temp_enum"),
            #     'rain_category': Enum(*RAIN_CATEGORIES, name="rain_enum"),
            #     'wind_category': Enum(*WIND_CATEGORIES, name="wind_enum")
            # }
        )
        print(f"Successfully loaded {len(df_weather)} weather records into PostgreSQL!")
        
    except Exception as e:
        session.rollback()
        print(f"Error loading data: {e}")
    finally:
        session.close()



# _______________________________________________________
if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:2004@localhost:5432/meteorisk")
    # db_url = "postgresql://postgres:2004@localhost:5432/meteorisk"
    gold = pd.read_csv('Gold/gold_data.csv')
    load_to_postgres(gold, db_url)