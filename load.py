from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship

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