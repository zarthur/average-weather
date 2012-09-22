"""Generate plots for high/low temperatures using matplotlib

Using javascript to generate plots didn't work due to a problem
with JQuery Mobile.  Thus, static images are generated using
matplotlib.
"""

import os
import pylab


class Plot():
    """Class to generate and save matplotlib plots of temperatures"""
    def __init__(self):
        """Set the counter to zero."""
        self._counter = 0

    def _get_counter(self):
        """Keep track of file counter.  Ensures that there are never
        more plot files than the number specified in the code.
        """
        counter = self._counter
        self._counter += 1 if self._counter < 100 else 0
        return counter

    def makeplot(self, path, width, labels, *y):
        """Generate plot with lables and various data; save to
        specified path and return filename
        """
        x = range(len(labels))
        pylab.figure(figsize=(width, width))
        window = [min(x), max(x)]
        y_extrema = None
        for ydata in y:
            y_min = min(ydata)
            y_max = max(ydata)
            y_extrema = [min([y_extrema[0], y_min]),
                            max([y_extrema[1], y_max])] \
                        if y_extrema else [y_min, y_max]
        window.extend(y_extrema)
        xm, xM, ym, yM = window
        window = [xm, xM, ym - 10, yM + 10]
        pylab.axis(window)
        pylab.hold(True)
        colors = ['b', 'r']
        for i, y_data in enumerate(y):
            plotcolor = colors[i % 2]
            pylab.plot(x, y_data, plotcolor)
        pylab.xticks(x, labels, rotation='vertical')
        #pylab.legend(('Low', 'High'))
        file_name = ''.join([str(self._get_counter()), '.png'])
        file_path = os.path.join(path, file_name)
        pylab.savefig(file_path)
        pylab.hold(False)
        pylab.close('all')
        return file_name
