import pandas as  pd
import numpy as  np



cities = pd.read_csv('ma.csv')
weather = pd.read_json('raw_data.json')
data = pd.merge(cities, weather, on='city', how='outer')
data.to_csv('data.csv', index=False)

