"""Generate a website to prompt a user for a zip code and
return weather information with supplied zip code.
"""

import cherrypy
import os

from mako.lookup import TemplateLookup

import makeplot
import query

DPI = 96

lookup = TemplateLookup(directories=['templates'])


def mean(alist):
    """Returns the mean of a list of values."""
    alist = [float(x) for x in alist]
    return sum(alist) / len(alist)


def render(*args, **kwargs):
    """Shortcut render function for use with mako"""
    page = args[0]
    tmpl = lookup.get_template(page)
    return tmpl.render(**kwargs)


class AverageWeather(object):
    """Main class; represents the website."""
    def __init__(self):
        """Set the plotter"""
        self.plotter = makeplot.Plot()

    @cherrypy.expose
    def index(self):
        """index.html page for site"""
        cherrypy.response.headers['Cache-Control'] = "no-cache"
        return render('index.html')

    @cherrypy.expose
    def get_weather(self, *args, **kwargs):
        """get zip_code from form, query services, generate plot, and
        render summary.html with necessary parameters.
        """
        cherrypy.response.headers['Cache-Control'] = "no-cache"
        zip_code = kwargs.get('zip_code')
        if not zip_code:
            return render('index.html')

        zip_code = zip_code[:5] if (zip_code and len(zip_code) > 5) \
                    else zip_code
        zip_test = zip_code and zip_code.isdigit()
        zip_code = int(zip_code) if zip_test else 12345
        winwidth = int(kwargs.get('winwidth', 3))
        winwidth = min([round((winwidth - 20) / DPI), 5])

        gw = query.GetWeather(zip_code)
        results = gw.get_all()

        cites = [x['cite'] for x in results]
        services = [x['source'] for x in results]
        current = [x['data'].pop('current', None) for x in results]
        forecast = [x['data'] for x in results]

        lows, highs = [], []

        dates = []
        days = []
        for i, source in enumerate(forecast):
            for key in source.keys():
                if key not in dates:
                    dates.append(key)
                    days.append(source[key]['day'])

        for date in dates:
            low_list = []
            high_list = []
            for source in forecast:
                if date in source:
                    low_list.append(source[date]['low'])
                    high_list.append(source[date]['high'])
            lows.append(low_list)
            highs.append(high_list)

        mean_lows = [mean(x) for x in lows]
        mean_highs = [mean(x) for x in highs]

        plotfile = self.plotter.makeplot('./templates/public/plots', winwidth,
                                         days, mean_lows, mean_highs)

        return render('summary.html', cites=cites, current=current, dates=dates,
                      days=days, forecast=forecast,  mean_highs=mean_highs,
                      mean_lows=mean_lows, plotfile=plotfile,
                      services=services, zip_code=zip_code)


def main():
    """start the server"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080})
    conf = {
        '/': {'tools.caching.on': False},
        '/public': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(current_dir, 'templates/public')
        }
    }
    cherrypy.quickstart(AverageWeather(), '/', config=conf)

if __name__ == '__main__':
    main()
