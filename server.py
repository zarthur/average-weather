import cherrypy

from mako.template import Template
from mako.lookup import TemplateLookup

import query

lookup = TemplateLookup(directories=['templates'])

def render(*args, **kwargs):
    page = args[0]
    tmpl = lookup.get_template(page)
    return tmpl.render(**kwargs)

class AverageWeather(object):
    @cherrypy.expose
    def index(self):
        return render('index.html')

    @cherrypy.expose
    def get_weather(self, *args, **kwargs):
        print(kwargs.get('zip_code'))

def main():
    cherrypy.quickstart(AverageWeather())

if __name__ == '__main__':
    main()
