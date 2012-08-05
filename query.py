"""Provides interface to Google and Yahoo for weather querying.
"""

import json
import urllib.request
import xml.etree.ElementTree as etree

from collections import OrderedDict


GOOGLE_URL = 'http://www.google.com/ig/api?weather={zip_code}'
YAHOO_URL = 'http://query.yahooapis.com/v1/public/yql?'\
            'q=select%20item%20from%20weather.forecast%20where%20'\
            'location=%22{zip_code}%22&format=json'

class GetWeather(object):
    """Class to query weather services"""
    def __init__(self, zip_code):
        self.zip_code = zip_code

    @staticmethod
    def _gen_data_dict(source, data):
        """Create a dictionary with sources as keys and data(temps) as values
        """
        data_dict = {
            'source': source,
            'data': data
        }
        return data_dict

    @staticmethod
    def _get_response(req_url, json_resp=True):
        """Get response from a sepecified URL; Process JSON if response
        is JSON, else return data from URL request
        """
        request = urllib.request.Request(req_url)
        req_data = urllib.request.urlopen(request)
        data = json.loads(req_data.read().decode()) \
                if json_resp else etree.parse(req_data)
        return data

    def get_all(self):
        """Query the services and unpack the results."""
        services = [
            self.get_google_weather,
            self.get_yahoo_weather
        ]
        results = [x() for x in services]

        return results


    def get_google_weather(self):
        """Query Google for weather information, returns results dictionary."""
        forecast_dict = OrderedDict()
        req_url = GOOGLE_URL.format(zip_code=self.zip_code)
        xml_data = self._get_response(req_url, json_resp=False)
        root = xml_data.getroot()

        container = root.getchildren()[0]

        current = container.find('current_conditions')
        print(current)
        icon_path = urllib.request.urljoin(
                        'http://www.google.com',
                        current.find('icon').attrib['data']
        )
        forecast_dict['current'] = {
            'condition': current.find('condition').attrib['data'],
            'temp': current.find('temp_f').attrib['data'],
            'icon': icon_path,
            'humidity': current.find('humidity').attrib['data'].split(':')[-1],
            'wind': current.find('wind_condition').attrib['data'].split(':')[-1],
        }

        forecasts = container.findall('forecast_conditions')
        for forecast in forecasts:
            icon_path = urllib.request.urljoin(
                            'http://www.google.com',
                            forecast.find('icon').attrib['data']
            )

            forecast_dict[forecast.find('day_of_week').attrib['data']] = {
                'low': int(forecast.find('low').attrib['data']),
                'high': int(forecast.find('high').attrib['data']),
                'condition': forecast.find('condition').attrib['data'],
                'icon': icon_path
            }

        google_dict = self._gen_data_dict('google', forecast_dict)

        return google_dict

    def get_yahoo_weather(self):
        """Query Yahoo for weather information, returns results dictionary."""
        forecast_dict = OrderedDict()
        req_url = YAHOO_URL.format(zip_code=self.zip_code)
        json_data = self._get_response(req_url)

        current = json_data['query']['results']['channel']['item']['condition']
        forecast_dict['current'] = {
            'temp': current['temp'],
            'condition': current['text']
        }

        forecasts = json_data['query']['results']['channel']['item']['forecast']
        for forecast in forecasts:
            forecast_dict[forecast['day']] = {
                'low': forecast['low'],
                'high': forecast['high'],
                'condition': forecast['text']
            }

        yahoo_dict = self._gen_data_dict('yahoo', forecast_dict)

        return yahoo_dict

if __name__ == '__main__':
    gw = GetWeather(90210)
    results = gw.get_all()