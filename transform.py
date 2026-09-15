import pandas as  pd
import ast 


#_____________________________________
data = pd.read_csv('Bronz/data.csv')

#_____________________________________
# chosing the column we need 
data = data[['city', 'admin_name', 'weather']]

#_____________________________________
# transform the weather from str into dict
daily_info = data['weather'].apply(lambda x: ast.literal_eval(x)['daily'])

#_____________________________________
# transform the key, value into column
daily_info = pd.json_normalize(daily_info)

#_____________________________________
#replace the weather in data with the conlumn from weather->daily
data = data.drop(columns = 'weather')
data = pd.concat([data, daily_info], axis=1)



#_____________________________________
#the content of the added columns is a list so we exploded the values => have more rows + get rid of the lists values
weather_column = daily_info.columns
exploded_data = data.explode(weather_column.tolist(), ignore_index=True)

# print(test)
# print(weather_column)
# print(data)

#_____________________________________
#save the data as .csv files (saved in Silver)
data.to_csv('silver_data.csv', index=False)
exploded_data.to_csv('exploded_data.csv', index=False)

# print(data['weather'])
# print(daily_info)
# print(daily_info)


#_____________________________________
# weather code for support (incase i needed it)
weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",

    45: "Fog",
    48: "Depositing rime fog",

    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",

    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",

    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",

    66: "Light freezing rain",
    67: "Heavy freezing rain",

    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",

    77: "Snow grains",

    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",

    85: "Slight snow showers",
    86: "Heavy snow showers",

    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}