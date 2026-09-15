import pandas as  pd
import requests
import numpy as  np



cities = pd.read_csv('ma.csv')
# _______________________________________
# data from the json file
# weather = pd.read_json('raw_data.json')

# _______________________________________
url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 33.5992,
    "longitude": -7.62,
    "daily": [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "weather_code"
    ],
    "timezone": "auto"
}

response = requests.get(url, params=params)

print(response)
print(response.json())
# _______________________________________
# merge the cities&weather data
# data = pd.merge(cities, weather, on='city', how='outer')
# data.to_csv('data.csv', index=False)

