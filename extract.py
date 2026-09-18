import pandas as  pd
import requests
import shutil 




def transform():
    # _______________________________________
    cities = pd.read_csv('ma.csv')


    # _______________________________________
    url = "https://api.open-meteo.com/v1/forecast"
    extracted_data = []
    for index, row in cities.iterrows():
        params = {
            "latitude": row['lat'],
            "longitude": row['lng'],
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
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            res_json = response.json()
            
            # Attach city metadata
            res_json['city'] = row['city']
            res_json['lat'] = row['lat']
            res_json['lng'] = row['lng']
            res_json['admin_name'] = row.get('admin_name', '')
            
            extracted_data.append(res_json)
        except Exception as e:
            print(f"Error fetching data for {row['city']}: {e}")

    # Save untouched JSON/DF to Bronze layer
    bronze_df = pd.DataFrame(extracted_data)
    bronze_df.to_csv('Bronze/bronze_data.csv', index=False)
    print("Bronze extraction complete.")



if __name__ == "__main__":
    transform()