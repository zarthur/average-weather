#python 3

import json
import urllib.request
import xml.etree.ElementTree as etree

from collections import OrderedDict

from config import WUGROUND_KEY

class GetWeather(object):
    def __init__(self, zip_code):
        self.zip_code = zip_code

    @staticmethod
    def _gen_data_dict(source, data):
        data_dict = {
            'source': source,
            'data': data
        }
        return data_dict

    @staticmethod
    def _get_response(req_url, json_resp=True):
        request = urllib.request.Request(req_url)
        req_data = urllib.request.urlopen(request)
        data = json.loads(req_data.read().decode()) \
                if json_resp else etree.parse(req_data)
        return data

    def get_google_weather(self):
        forecast_dict = OrderedDict()
        req_url = 'http://www.google.com/ig/api?weather={zip_code}'\
                    .format(zip_code=self.zip_code)
        xml_data = self._get_response(req_url, json_resp=False)
        root = xml_data.getroot()
        container = root.getchildren()[0]
        forecasts = container.findall('forecast_conditions')
        for forecast in forecasts:
            forecast_dict[forecast.find('day_of_week').attrib['data']] = {
                'low': forecast.find('low').attrib['data'],
                'high': forecast.find('high').attrib['data'],
                'condition': forecast.find('condition').attrib['data']
            }

        google_dict = self._gen_data_dict('google', forecast_dict)

        return google_dict

    def get_wuground_weather(self):
        forecast_dict = OrderedDict()
        req_url = \
            'http://api.wunderground.com/api/{key}/forecast/q/{zip_code}.json'\
                .format(key=WUGROUND_KEY, zip_code=self.zip_code)
        json_data = self._get_response(req_url)
        forecasts = json_data['forecast']['simpleforecast']['forecastday']
        for forecast in forecasts:
            forecast_dict[forecast['date']['weekday_short']] = {
                'low': forecast['low']['fahrenheit'],
                'high': forecast['high']['fahrenheit'],
                'conditions': forecast['conditions']
            }

        wuground_dict = self._gen_data_dict('weather underground',
                                                forecast_dict)

        return wuground_dict

    def get_yahoo_weather(self):
        forecast_dict = OrderedDict()
        req_url = ''.join([
            'http://query.yahooapis.com/v1/public/yql?',
            'q=select%20item%20from%20weather.forecast%20where%20',
            'location=%22{zip_code}%22&format=json'\
            .format(zip_code=self.zip_code)
        ])
        json_data = self._get_response(req_url)
        forecasts = json_data['query']['results']['channel']['item']['forecast']
        for forecast in forecasts:
            forecast_dict[forecast['day']] = {
                'low': forecast['low'],
                'high': forecast['high'],
                'conditions': forecast['text']
            }

        yahoo_dict = self._gen_data_dict('yahoo', forecast_dict)

        return yahoo_dict
