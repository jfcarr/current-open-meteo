#!/usr/bin/env -S uv run -q -s

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "geopy",
#     "argparse"
# ]
# ///

from datetime import datetime
from geopy.geocoders import Nominatim
import argparse
import json
import requests

degree_sign = u'\N{DEGREE SIGN}'
is_debug = False  # Must be False for production!

class OpenMeteoManager:
    def __init__(self, response_text):
        self.response_text = response_text
        self.data_object = json.loads(self.response_text)

    def get_current_time(self):
        '''
        Get the current time from the API response and format it as 12 hour am/pm.
        '''
        datetime_string = self.data_object['current']['time']
        dt = datetime.fromisoformat(datetime_string)

        time_12_hour_format = dt.strftime("%I:%M %p").lstrip('0')

        return time_12_hour_format

    def get_temperature_description(self):
        '''
        Get actual and apparent temperature from the API response, round them to nearest value, and
        return a formatted string.
        '''
        temperature = round(self.data_object['current']['temperature_2m'], 0)
        formatted_temperature = f"{temperature:.2f}".rstrip('0').rstrip('.')
            
        apparent_temperature = round(self.data_object['current']['apparent_temperature'], 0)
        formatted_apparent_temperature = f"{apparent_temperature:.2f}".rstrip('0').rstrip('.')

        return f"{formatted_temperature}{degree_sign} (feels like {formatted_apparent_temperature}{degree_sign})"

    def get_humidity_and_dewpoint(self):
        '''
        Get apparent humidity percentage and dew point temperature from API response.
        '''
        humidity = self.data_object['current']['relative_humidity_2m']
        dewpoint = round(self.data_object['current']['dew_point_2m'], 0)
        formatted_dewpoint = f"{dewpoint:.2f}".rstrip('0').rstrip('.')

        return f"Relative humidity is {humidity}%, dew point is {formatted_dewpoint}{degree_sign}"

    def get_wso_description(self):
        '''
        Get the WMO weather code from the API response and use it to look up a friendly description
        of weather conditions.
        '''
        is_day = self.data_object['current']['is_day']

        weather_code = self.data_object['current']['weather_code']
        description = OpenMeteoData.wmo_weather_codes().get(str(weather_code))

        if description:
            if "|" in description:
                description = description.split("|")
                description = description[0] if is_day == 1 else description[1]
        else:
            description = "Unknown"
        
        return description

    def get_cloud_cover_description(self):
        '''
        Get the cloud cover description from the API response.
        '''
        return f"{self.data_object['current']['cloud_cover']}% cloud cover"

    def get_wind_description(self):
        '''
        Get the wind and wind gust speed.
        '''
        wind = round(self.data_object['current']['wind_speed_10m'], 0)
        wind = f"{wind:.2f}".rstrip('0').rstrip('.')

        wind_gust = round(self.data_object['current']['wind_gusts_10m'], 0)
        wind_gust = f"{wind_gust:.2f}".rstrip('0').rstrip('.')

        wind_direction = OpenMeteoHelpers.get_cardinal_direction(self.data_object['current']['wind_direction_10m'])

        wind_description = f"Wind: {wind} mph ({wind_direction}), gusting to {wind_gust} mph"

        return wind_description

    def get_precipitation_probability(self):
        '''
        Get precipitation likelihood and return formatted description
        '''
        precipitation_probability = self.data_object['current']['precipitation_probability']

        return f"Precipitation probability is {precipitation_probability}%"

    def get_formatted_low_temperature(self):
        '''
        Get the daily low temperature.
        '''
        temperature = round(self.data_object['daily']['temperature_2m_min'][0], 0)
        formatted_temperature = f"{temperature:.2f}".rstrip('0').rstrip('.')

        return f"min: {formatted_temperature}{degree_sign}"

    def get_formatted_high_temperature(self):
        '''
        Get the daily high temperature.
        '''
        temperature = round(self.data_object['daily']['temperature_2m_max'][0], 0)
        formatted_temperature = f"{temperature:.2f}".rstrip('0').rstrip('.')

        return f"max: {formatted_temperature}{degree_sign}"

    def get_sunrise(self):
        '''
        Get the time of today's sunrise.
        '''
        datetime_string = self.data_object['daily']['sunrise'][0]
        dt = datetime.fromisoformat(datetime_string)

        time_12_hour_format = dt.strftime("%I:%M %p").lstrip('0')

        return time_12_hour_format

    def get_sunset(self):
        '''
        Get the time of today's sunset.
        '''
        datetime_string = self.data_object['daily']['sunset'][0]
        dt = datetime.fromisoformat(datetime_string)

        time_12_hour_format = dt.strftime("%I:%M %p").lstrip('0')

        return time_12_hour_format
    
    def get_forecast(self, day_number):
        daily_data = self.data_object.get('daily')

        date_object = datetime.strptime(daily_data['time'][day_number], "%Y-%m-%d")
        day_of_week = date_object.strftime("%a")

        high_temperature = round(daily_data['temperature_2m_max'][day_number], 0)
        formatted_high_temperature = f"{high_temperature:.2f}".rstrip('0').rstrip('.')

        low_temperature = round(daily_data['temperature_2m_min'][day_number], 0)
        formatted_low_temperature = f"{low_temperature:.2f}".rstrip('0').rstrip('.')

        forecast_description = OpenMeteoData.wmo_weather_codes().get(str(daily_data['weather_code'][day_number]))

        precip = f"{daily_data['precipitation_probability_mean'][day_number]}% precip"

        return f"{day_of_week}: {formatted_high_temperature}{degree_sign}/{formatted_low_temperature}{degree_sign}, {forecast_description} ({precip})"

class OpenMeteoData:
    @classmethod
    def wmo_weather_codes(cls) -> dict:
        # https://gist.github.com/stellasphere/9490c195ed2b53c707087c8c2db4ec0c
        return {
            "0": "Sunny|Clear",
            "1": "Mainly Sunny|Mainly Clear",
            "2": "Partly Cloudy",
            "3": "Cloudy",
            "45": "Foggy",
            "48": "Rime Fog",
            "51": "Light Drizzle",
            "53": "Drizzle",
            "55": "Heavy Drizzle",
            "56": "Light Freezing Drizzle",
            "57": "Freezing Drizzle",
            "61": "Light Rain",
            "63": "Rain",
            "65": "Heavy Rain",
            "66": "Light Freezing Rain",
            "67": "Freezing Rain",
            "71": "Light Snow",
            "73": "Snow",
            "75": "Heavy Snow",
            "77": "Snow Grains",
            "80": "Light Showers",
            "81": "Showers",
            "82": "Heavy Showers",
            "85": "Light Snow Showers",
            "86": "Snow Showers",
            "95": "Thunderstorm",
            "96": "Light Thunderstorms with Hail",
            "99": "Thunderstorm with Hail"
        }

class OpenMeteoHelpers:
    @staticmethod
    def find_location(latitude, longitude):
        '''
        Use the GeoPy geolocator to get location information based on latitude and longitude.
        '''
        geolocator = Nominatim(user_agent="openMeteoCli")
        location = geolocator.reverse(f"{latitude}, {longitude}")

        if location:
            return f"{location.raw['address']['county']}, {location.raw['address']['postcode']}"
        else:
            return "Unknown location"

    @staticmethod
    def get_cardinal_direction(azimuth):
        '''
        Give an azimuth value in degrees, return a cardinal direction, e.g., "NE".
        '''
        if azimuth < 0 or azimuth >= 360:
            raise ValueError("Azimuth must be in the range [0, 360) degrees.")
        
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"
        ]
        
        index = round(azimuth / 22.5) % 16
    
        return directions[index]

def main():
    parser = argparse.ArgumentParser(description='A simple argument parser example.')
    parser.add_argument('--latitude', type=float, help='Your latitude, e.g. 39.6142', required=True)
    parser.add_argument('--longitude', type=float, help='Your longitude, e.g. -84.5560', required=True)
    parser.add_argument('--timezone', type=str, help='Your time zone, in tz identifier format, e.g. "America/New_York"', required=True)
    args = parser.parse_args()

    current_parameter = ",".join(
        [
            "is_day",
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "dew_point_2m",
            "cloud_cover",
            "wind_speed_10m",
            "wind_gusts_10m",
            "wind_direction_10m",
            "precipitation",
            "snowfall",
            "precipitation_probability",
            "rain",
            "showers",
            "weather_code",
            "snow_depth",
            "visibility"
        ]
    )

    daily_parameter = ",".join(
        [
            "temperature_2m_max",
            "temperature_2m_min",
            "sunrise",
            "sunset",
            "rain_sum",
            "snowfall_sum",
            "precipitation_probability_mean",
            "weather_code"
        ]
    )

    location_name = "Unknown location"
    try:
        location_name = OpenMeteoHelpers.find_location(args.latitude, args.longitude)
    except:
        pass

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast?" + 
            f"latitude={args.latitude}&longitude={args.longitude}&" + 
            "temperature_unit=fahrenheit&" +
            "wind_speed_unit=mph&" +
            f"timezone={args.timezone}&" +
            f"current={current_parameter}&" +
            f"daily={daily_parameter}"
        )

        if response.status_code == 200:
            if is_debug:
                print (json.dumps(response.json(), indent=4))

            om_mgr = OpenMeteoManager(response.text)

            print(f"{location_name} @ {om_mgr.get_current_time()}")
            print(f"  {om_mgr.get_temperature_description()}")
            print(f"  {om_mgr.get_wso_description()}, {om_mgr.get_cloud_cover_description()}")
            print(f"  {om_mgr.get_humidity_and_dewpoint()}")
            print(f"  {om_mgr.get_wind_description()}")
            print(f"  {om_mgr.get_precipitation_probability()}")
            print("  ----")
            print(f"  sunrise: {om_mgr.get_sunrise()} / sunset: {om_mgr.get_sunset()}")
            print("  ----")
            print(f"  {om_mgr.get_forecast(0)}")
            print(f"  {om_mgr.get_forecast(1)}")
            print(f"  {om_mgr.get_forecast(2)}")
            print(f"  {om_mgr.get_forecast(3)}")
            print(f"  {om_mgr.get_forecast(4)}")
        else:
            print("Failed to retrieve weather data.")
            print(f"Status code: {response.status_code}")
    except Exception as ex:
        print("An error occurred:")
        print(f"{ex}")

if __name__ == "__main__":
    main()
