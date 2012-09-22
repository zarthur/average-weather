"""Provides interface to Google and Yahoo for weather querying.
"""

import datetime
import json
import urllib.request
import xml.etree.ElementTree as etree

from collections import OrderedDict


DAYDICT = {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thu',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun'
}

# Google weather url, returns XML
GOOGLE_URL = 'http://www.google.com/ig/api?weather={zip_code}'

# Yahoo weather url, returns JSON
YAHOO_URL = 'http://query.yahooapis.com/v1/public/yql?'\
            'q=select%20item%20from%20weather.forecast%20where%20'\
            'location=%22{zip_code}%22&format=json'

# yr.no weather url, returns XML
YR_NO_URL = 'http://www.yr.no/place/{country}/{admin_name1}/{place_name}/'\
            'forecast.xml'

# Place info from postal code, returns JSON
ZIP_PLACE_URL = 'http://ws.geonames.org/postalCodeSearchJSON?formatted=true'\
                '&postalcode={zip_code}&maxRows=1&style=full'

# Country name from country code url, returns JSON
COUNTRY_URL = 'http://ws.geonames.org/countryInfoJSON?formatted=true'\
              '&lang=en&country={country_code}&style=full'


def average_date(date_str_1, date_str_2):
    """Return midpoint date between two dates"""
    date1 = datetime.datetime.strptime(date_str_1, '%Y-%m-%d')
    date2 = datetime.datetime.strptime(date_str_2, '%Y-%m-%d')
    diff = date2 - date1
    new_date = date1 + diff

    return new_date.strftime('%Y-%m-%d')


def c_to_f(cel):
    """Convert celsius to fahrenheit (what an awful word to spell)"""
    return 9 / 5 * float(cel) + 32


def date_to_day(date_string):
    """Converts a date string in the form YYYY-MM-DD to a weekday
    and returns the weekday string
    """
    date = [int(x) for x in date_string.split('-')]
    day = DAYDICT[datetime.date(*date).weekday()]
    return day


def find_most_frequent(dict):
    """Replaces list used for dictionary value with element
    that appears most frequently; if none found, uses middle element
    """
    temp_dict = OrderedDict()
    for key, value in dict.items():
        counts = [value.count(x) for x in value]
        maxcount = max(counts)
        if maxcount > 1:
            temp_dict[key] = value[counts.index(maxcount)]
        else:
            index = len(value) // 2
            temp_dict[key] = value[index]
    return temp_dict


def get_response(req_url, json_resp=True):
    """Get response from a sepecified URL; Process JSON if response
    is JSON, else return data from URL request
    """
    request = urllib.request.Request(req_url)
    req_data = urllib.request.urlopen(request)
    data = json.loads(req_data.read().decode()) \
            if json_resp else etree.parse(req_data)
    return data


def is_today_or_earlier(from_date, to_date):
    """Test if dates are before today or today"""
    from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
    today = datetime.datetime.today()

    return from_date <= today or to_date <= today


def update_dict_list(dictionary, key, value):
    """Update a dictionary of lists"""
    if key not in dictionary:
        dictionary[key] = []
    dictionary[key].append(value)
    return dictionary


def xml_to_dict(el):
    """Convert XML to python dictionary.
    Modified from http://stackoverflow.com/a/2303733/1298998
    """
    # The dict looks like a mess but it is easier to work
    # with when developing, in my opinion.
    d={el.tag: {}}
    if el.text:
        d[el.tag]['text'] = el.text
    if el.attrib:
        d[el.tag]['attrib'] = el.attrib
    d[el.tag]['children'] = [xml_to_dict(c) for c in el.getchildren()]
    return d


class GetWeather(object):
    """Class to query weather services"""
    def __init__(self, zip_code):
        self.zip_code = zip_code

    @staticmethod
    def _gen_data_dict(source, data, cite):
        """Create a dictionary with sources as keys and data(temps) as values
        """
        data_dict = {
            'source': source,
            'data': data,
            'cite': cite
        }
        return data_dict

    def get_all(self):
        """Query the services and unpack the results."""
        services = [
            # self.get_google_weather,
            self.get_yahoo_weather,
            self.get_yrno_weather
        ]
        results = [x() for x in services]
        return results

    def get_google_weather(self):
        """Query Google for weather information, returns results dictionary."""
        forecast_dict = OrderedDict()
        req_url = GOOGLE_URL.format(zip_code=self.zip_code)
        xml_data = get_response(req_url, json_resp=False)
        root = xml_data.getroot()

        container = root.getchildren()[0]

        current = container.find('current_conditions')
        icon_path = urllib.request.urljoin(
                        'http://www.google.com',
                        current.find('icon').attrib['data']
        )
        forecast_dict['current'] = {
            'condition': current.find('condition').attrib['data'],
            'temp': current.find('temp_f').attrib['data'],
            'icon': icon_path,
            'humidity': current.find('humidity').attrib['data'].split(':')[-1],
            'wind': current.find('wind_condition').attrib['data']
                    .split(':')[-1]
        }

        forecasts = container.findall('forecast_conditions')
        for forecast in forecasts:
            icon_path = urllib.request.urljoin(
                            'http://www.google.com',
                            forecast.find('icon').attrib['data']
            )

            # key needs to be verified if google is used again
            forecast_dict[forecast.find('date').attrib['data']] = {
                'day': forecast.find('day_of_week').attrib['data'],
                'low': int(forecast.find('low').attrib['data']),
                'high': int(forecast.find('high').attrib['data']),
                'condition': forecast.find('condition').attrib['data'],
                'icon': icon_path
            }

        google_dict = self._gen_data_dict('google', forecast_dict)

        return google_dict

    def get_yahoo_weather(self, get_cite=False):
        """Query Yahoo for weather information, returns results dictionary."""
        forecast_dict = OrderedDict()
        req_url = YAHOO_URL.format(zip_code=self.zip_code)
        json_data = get_response(req_url)

        if get_cite:
            cite = {'text': 'Yahoo Weather', 'link': json_data['query']\
                    ['results']['channel']['item']['link'].split('*')[-1]
}
        current = json_data['query']['results']['channel']['item']['condition']
        forecast_dict['current'] = {
            'temp': current['temp'],
            'condition': current['text']
        }

        forecasts = json_data['query']['results']['channel']['item']\
                    ['forecast']

        for forecast in forecasts:
            date = datetime.datetime.strptime(forecast['date'], '%d %b %Y')\
                    .strftime('%Y-%m-%d')
            forecast_dict[date] = {
                'day': forecast['day'],
                'low': forecast['low'],
                'high': forecast['high'],
                'condition': forecast['text']
            }

        cite = {'text': 'yahoo', 'url': 'http://www.yahoo.com'}

        yahoo_dict = self._gen_data_dict('yahoo', forecast_dict, cite)

        return yahoo_dict

    def get_yrno_weather(self):
        """Query yr.no for weather information, returns results dictionary.

        Current conditions are not available so none are record for use.
        """
        # first, get place names from zip code
        place_json = get_response(
                        ZIP_PLACE_URL.format(zip_code=self.zip_code))
        place_json = place_json['postalCodes'][0]
        place_name = place_json['placeName']
        admin_name1 = place_json['adminName1']
        country_code = place_json['countryCode']

        country_json = get_response(
            COUNTRY_URL.format(country_code=country_code))
        country_json = country_json['geonames'][0]
        country = country_json['countryName'].replace(' ', '%20')

        # get data from yr.no
        yrno_xml = get_response(YR_NO_URL.format(
            country=country, admin_name1=admin_name1, place_name=place_name),
            json_resp=False)
        yrno_xml = yrno_xml.getroot()
        yrno_dict = xml_to_dict(yrno_xml)


        # return citation text and url, per yr.no terms
        cite = yrno_dict['weatherdata']['children'][1]['credit']\
                        ['children'][0]['link']['attrib']

        forecast_data = yrno_dict['weatherdata']['children'][5]['forecast']\
                                 ['children'][0]['tabular']['children']

        # remove data from past
        remove_list = []
        for i, time_period in enumerate(forecast_data[:]):
            data = time_period['time']
            from_time = data['attrib']['from'].split('T')[0]
            to_time = data['attrib']['to'].split('T')[0]

            # skip if before today
            if is_today_or_earlier(from_time, to_time):
                remove_list.append(i)

        for i in sorted(remove_list, reverse=True):
            forecast_data.pop(i)

        forecast_dict = OrderedDict()

        # record future conditions
        temps = OrderedDict()
        conds = OrderedDict()
        for time_period in forecast_data:
            data = time_period['time']

            from_time = data['attrib']['from'].split('T')[0]
            to_time = data['attrib']['to'].split('T')[0]
            ave_date = average_date(from_time, to_time)

            condition = data['children'][0]['symbol']['attrib']['name']
            temp = c_to_f(int(data['children'][4]['temperature']\
                                    ['attrib']['value']))

            temps = update_dict_list(temps, ave_date, temp)
            conds = update_dict_list(conds, ave_date, condition)
            # if from_time != to_time:
            #     temps = update_dict_list(temps, to_time, temp)
            #     conds = update_dict_list(conds, to_time, condition)

        lowhigh = OrderedDict([(date, (int(min(temps[date])),
                                int(max(temps[date])))) for date in temps])

        conds = find_most_frequent(conds)
        keylist = list(conds.keys())

        # put data into dict
        for i in range(len(keylist)):
            key = keylist[i]
            day = date_to_day(key)
            forecast_dict[key] = {
                'day': day,
                'low': lowhigh[key][0],
                'high': lowhigh[key][1],
                'condition': conds[key]
            }

        yrno_dict = self._gen_data_dict('yr.no', forecast_dict, cite)

        return yrno_dict

if __name__ == '__main__':
    gw = GetWeather(90210)
    results = gw.get_all()
