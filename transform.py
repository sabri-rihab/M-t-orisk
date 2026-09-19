import pandas as  pd
import ast 


def transform() :
    #_____________________________________
    data = pd.read_csv('Bronz/bronze_data.csv')

    #_____________________________________
    # chosing the column we need 
    meta_data = data[['city', 'admin_name','lat', 'lng', 'daily']]

    #_____________________________________
    # transform the daily from str into dict
    # check if daily is really a string, if it was a dict literal_eval will throw an error
    daily = meta_data['daily'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x) 

    #_____________________________________
    # transform the key, value into column
    daily = pd.json_normalize(daily)

    #_____________________________________
    #replace the weather in data with the conlumn from weather->daily
    meta_data = meta_data.drop(columns = 'daily')
    meta_data = pd.concat([meta_data, daily], axis=1)

    #_____________________________________
    #the content of the added columns is a list so we exploded the values => have more rows + get rid of the lists values
    weather_column = daily.columns
    silver_df = meta_data.explode(weather_column.tolist(), ignore_index=True)
    #_____________________________________
    # change the column 'time' to prevent error in db
    # turn the time from str to datetime + chnage forma to adapt to db
    silver_df = silver_df.rename(columns={'time': 'forecast_date'})
    silver_df['forecast_date'] = pd.to_datetime(silver_df['forecast_date'], errors= "coerce") 

    #_____________________________________
    # replace the missing dates
    date_offset = silver_df.groupby('city')['forecast_date']\
        .transform(lambda g: g.groupby((~g.isnull()).cumsum()).cumcount())
    silver_df['forecast_date'] = silver_df.groupby('city')['forecast_date']\
        .transform(lambda g: g.ffill()) + pd.to_timedelta(date_offset, unit='D')
    silver_df['forecast_date'] = silver_df.groupby('city')['forecast_date'].transform(lambda g: g.bfill())

    silver_df["forecast_date"] = silver_df["forecast_date"].dt.strftime('%Y-%m-%d')


    # ________________________________
    # drop duplicated rows
    silver_df = silver_df.drop_duplicates(subset=['city', 'forecast_date'])

    #_____________________________________
    # turn nueric values from str to numiric 
    # replace nonne values
    numeric_cols = [c for c in weather_column if c != 'time']
    for col in numeric_cols:
        silver_df[col] = pd.to_numeric(silver_df[col], errors='coerce')
        silver_df[col] = silver_df.groupby('city')[col]\
                        .transform(lambda g: g.interpolate(method='linear').ffill().bfill())




    # ___________________________________________________
    # ________________( quality check )__________________
    def validate_data_quality(df):
        assert df["temperature_2m_max"].between(-20, 60).all(), ("Data Quality Error: Extreme temperature out of bounds!")
        assert (df["precipitation_sum"].ge(0).all()), "Data Quality Error: Negative precipitation detected!"
        assert (df["wind_speed_10m_max"].ge(0).all()), "Data Quality Error: Negative wind speed detected!"
        assert (df["forecast_date"].notnull().all()), "Data Quality Error: Null forecast dates found!"

        print("checks passed successfully ^^ ")
    #_____________________________________
    #save the data as .csv files (saved in Silver)
    validate_data_quality(silver_df)
    silver_df.to_csv('Silver/silver_data.csv', index=False)
    print('silver stage : done!')

    # print(test)
    # print(weather_column)
    # print(data['weather'])
    # print(daily_info)


if __name__ == "__main__":
    transform()


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