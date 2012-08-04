#python 3

import json
import urllib.request
import xml.etree.ElementTree as etree

from collections import OrderedDict

from config import WUGROUND_KEY

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

    @staticmethod
    def _get_data_list(dataset, value, isint=False):
        datalist = [dataset['data'][x].get(value) for x in dataset['data']]
        datalist = [int(x) for x in datalist] if isint else datalist
        return [dataset['source'], datalist]

    def get_all(self):
        """Query all the services! and return days, lows, highs, and
        conditions.
        """
        services = [
            self.get_google_weather,
            #self.get_wuground_weather,
            self.get_yahoo_weather
        ]
        results = [x() for x in services]
        current, results = zip(*results)
        result_count = [len(x['data']) for x in results]
        result_max_index = result_count.index(max(result_count))
        days = list(results[result_max_index]['data'].keys())
        highs = []
        lows = []
        conditions = []
        icons      = []

        for dataset in results:
            highs.append(self._get_data_list(dataset, 'high', isint=True))
            lows.append(self._get_data_list(dataset, 'low', isint=True))
            conditions.append(self._get_data_list(dataset, 'condition'))
            icons.append(self._get_data_list(dataset, 'icon'))

        return current, days, lows, highs, conditions, icons


    def get_google_weather(self):
        forecast_dict = OrderedDict()
        req_url = 'http://www.google.com/ig/api?weather={zip_code}'\
                    .format(zip_code=self.zip_code)
        xml_data = self._get_response(req_url, json_resp=False)
        root = xml_data.getroot()

        container = root.getchildren()[0]

        current = container.find('current_conditions')
        print(current)
        current = current.find('temp_f').attrib['data']

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
        current_dict = self._gen_data_dict('google', current)

        return current_dict, google_dict

    def get_wuground_weather(self):
        forecast_dict = OrderedDict()
        req_url = \
            'http://api.wunderground.com/api/{key}/forecast/q/{zip_code}.json'\
                .format(key=WUGROUND_KEY, zip_code=self.zip_code)
        json_data = self._get_response(req_url)
        forecasts = json_data['forecast']['simpleforecast']['forecastday']
        for forecast in forecasts:
            forecast_dict[forecast['date']['weekday_short']] = {
                'low': int(forecast['low']['fahrenheit']),
                'high': int(forecast['high']['fahrenheit']),
                'condition': forecast['conditions']
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
        current = json_data['query']['results']['channel']['item']['condition']['temp']
        forecasts = json_data['query']['results']['channel']['item']['forecast']
        for forecast in forecasts:
            forecast_dict[forecast['day']] = {
                'low': forecast['low'],
                'high': forecast['high'],
                'condition': forecast['text']
            }

        yahoo_dict = self._gen_data_dict('yahoo', forecast_dict)
        current_dict = self._gen_data_dict('yahoo', current)

        return current_dict, yahoo_dict
