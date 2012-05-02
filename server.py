import cherrypy
import os

from mako.template import Template
from mako.lookup import TemplateLookup

import makeplot
import query

lookup = TemplateLookup(directories=['templates'])

def mean(alist):
    return sum(alist)/len(alist)

def mean_temps(temps):
    """calulate mean temperatures, return number of sources and means"""
    means = []
    services, temp_lists = zip(*temps)
    max_length = max([len(x) for x in temp_lists])
    for i in range(max_length):
        temporary = []
        for tlist in temp_lists:
            if len(tlist) > i:
                temporary.append(tlist[i])
        means.append((len(temporary), round(mean(temporary))))
    return means

def render(*args, **kwargs):
    """shortcut render function for use with mako"""
    page = args[0]
    tmpl = lookup.get_template(page)
    return tmpl.render(**kwargs)


class AverageWeather(object):
    def __init__(self):
        self.plotter = makeplot.Plot()

    @cherrypy.expose
    def index(self):
        """index.html page for site"""
        return render('index.html')

    @cherrypy.expose
    def get_weather(self, *args, **kwargs):
        """get zip_code from form, query services, generate plot, and
        render summary.html with necessary parameters.
        """
        zip_code = kwargs.get('zip_code')
        zip_code = zip_code[:5] if (zip_code and len(zip_code) > 5) else zip_code
        zip_test = zip_code and zip_code.isdigit()
        zip_code = int(zip_code) if zip_test else 12345
        gw = query.GetWeather(zip_code)
        days, lows, highs, conditions = gw.get_all()

        services, *junk = zip(*lows)

        mean_lows = mean_temps(lows)
        mean_highs = mean_temps(highs)

        junk, lmean = zip(*mean_lows)
        junk, hmean = zip(*mean_highs)

        plotfile = self.plotter.makeplot('./templates/public/plots', 
                                         days, lmean, hmean)

        #data passed to summary is a bit of a mess and should be reformatted
        return render('summary.html', services, days=days, lows=lows,
                      highs=highs, mean_lows=mean_lows, mean_highs=mean_highs,
                      conditions=conditions, zip_code=zip_code, 
                      plotfile=plotfile)

def main():
    """start the server"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update({'server.socket_host': '127.0.0.1',
                            'server.socket_port': 8080})
    conf = {'/public': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'templates/public')}}
    cherrypy.quickstart(AverageWeather(), '/' , config=conf)

if __name__ == '__main__':
    main()
