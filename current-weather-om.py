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

def find_location(latitude, longitude):
    '''
    Use the GeoPy geolocator to get location information based on latitude and longitude.
    '''
    geolocator = Nominatim(user_agent="openMeteoCli")
    location = geolocator.reverse(f"{latitude}, {longitude}")

    if location:
        if is_debug:
            print(location.raw)
        
        return location.address
    else:
        return "Unknown Location"

def get_current_time(response_text):
    '''
    Get the current time from the API response and format it as 12 hour am/pm.
    '''
    data_object = json.loads(response_text)
    datetime_string = data_object['current']['time']
    dt = datetime.fromisoformat(datetime_string)

    time_12_hour_format = dt.strftime("%I:%M %p")

    return time_12_hour_format

def get_temperature_description(response_text):
    '''
    Get actual and apparent temperature from the API response, round them to nearest value, and
    return a formatted string.
    '''
    data_object = json.loads(response_text)
    
    temperature = round(data_object['current']['temperature_2m'], 0)
    formatted_temperature = f"{temperature:.2f}".rstrip('0').rstrip('.')
        
    apparent_temperature = round(data_object['current']['apparent_temperature'], 0)
    formatted_apparent_temperature = f"{apparent_temperature:.2f}".rstrip('0').rstrip('.')

    return f"{formatted_temperature}{degree_sign} (feels like {formatted_apparent_temperature}{degree_sign})"

def get_wso_description(response_text):
    '''
    Get the WMO weather code from the API response and use it to look up a friendly description
    of weather conditions.
    '''
    # https://gist.github.com/stellasphere/9490c195ed2b53c707087c8c2db4ec0c
    wmo_weather_codes = {
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

    data_object = json.loads(response_text)

    is_day = data_object['current']['is_day']

    weather_code = data_object['current']['weather_code']
    description = wmo_weather_codes.get(str(weather_code))

    if description:
        if "|" in description:
            description = description.split("|")
            description = description[0] if is_day == 1 else description[1]
    else:
        description = "Unknown"
    
    return description

def get_cloud_cover_description(response_text):
    '''
    Get the cloud cover description from the API response.
    '''
    data_object = json.loads(response_text)

    return f"{data_object['current']['cloud_cover']}% cloud cover"

def get_wind_description(response_text):
    '''
    Get the wind and wind gust speed.
    '''
    data_object = json.loads(response_text)

    wind = round(data_object['current']['wind_speed_10m'], 0)
    wind = f"{wind:.2f}".rstrip('0').rstrip('.')

    wind_gust = round(data_object['current']['wind_gusts_10m'], 0)
    wind_gust = f"{wind_gust:.2f}".rstrip('0').rstrip('.')

    wind_description = f"Wind: {wind} mph, gusting to {wind_gust} mph"

    return wind_description

def get_formatted_low_temperature(response_text):
    '''
    Get the daily low temperature.
    '''
    data_object = json.loads(response_text)

    temperature = round(data_object['daily']['temperature_2m_min'][0], 0)
    formatted_temperature = f"{temperature:.2f}".rstrip('0').rstrip('.')

    return f"min: {formatted_temperature}{degree_sign}"

def get_formatted_high_temperature(response_text):
    '''
    Get the daily high temperature.
    '''
    data_object = json.loads(response_text)

    temperature = round(data_object['daily']['temperature_2m_max'][0], 0)
    formatted_temperature = f"{temperature:.2f}".rstrip('0').rstrip('.')

    return f"max: {formatted_temperature}{degree_sign}"

def get_sunrise(response_text):
    '''
    Get the time of today's sunrise.
    '''
    data_object = json.loads(response_text)

    datetime_string = data_object['daily']['sunrise'][0]
    dt = datetime.fromisoformat(datetime_string)

    time_12_hour_format = dt.strftime("%I:%M %p")

    return time_12_hour_format

def get_sunset(response_text):
    '''
    Get the time of today's sunset.
    '''
    data_object = json.loads(response_text)

    datetime_string = data_object['daily']['sunset'][0]
    dt = datetime.fromisoformat(datetime_string)

    time_12_hour_format = dt.strftime("%I:%M %p")

    return time_12_hour_format


def main():
    parser = argparse.ArgumentParser(description='A simple argument parser example.')
    parser.add_argument('--latitude', type=float, help='Your latitude, e.g. 39.6142', required=True)
    parser.add_argument('--longitude', type=float, help='Your longitude, e.g. -84.5560', required=True)
    parser.add_argument('--timezone', type=str, help='Your time zone, in tz identifier format, e.g. "America/New_York"', required=True)
    args = parser.parse_args()

    location_name = find_location(args.latitude, args.longitude)

    current_parameter = ",".join(
        [
            "is_day",
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
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
            "sunset"
        ]
    )

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

        print(f"{location_name} @ {get_current_time(response.text)}")
        print(f"  {get_temperature_description(response.text)}")
        print(f"  {get_wso_description(response.text)}, {get_cloud_cover_description(response.text)}")
        print(f"  {get_wind_description(response.text)}")
        print("  ----")
        print(f"  {get_formatted_low_temperature(response.text)} / {get_formatted_high_temperature(response.text)}")
        print(f"  sunrise: {get_sunrise(response.text)} / sunset: {get_sunset(response.text)}")
    else:
        print("Failed to retrieve weather data.")
        print(f"Status code: {response.status_code}")

if __name__ == "__main__":
    main()
