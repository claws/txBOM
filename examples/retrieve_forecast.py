#!/usr/bin/env python

'''
A demonstration of forecast retrieval.
'''

from twisted.internet import reactor, defer
import logging
import txbom.forecasts


forecast_id = "IDS10034"  # Adelaide forecast identifier


@defer.inlineCallbacks
def demo(forecast_id):

    forecast = yield txbom.forecasts.get_forecast(forecast_id)
    print "Received forecast text:"
    print forecast
    print "\n\n"

    # demonstrate how the forecast can be parsed into a dict
    forecastDict = txbom.forecasts.forecastToDict(forecast)
    forecastDictKeys = forecastDict.keys()
    forecastDictKeys.sort()
    print "Forecast dict:"
    for k in forecastDictKeys:
        print "%s : %s" % (k, forecastDict[k])
    print "\n\n"

    # this is the end of the test, stop reactor to finish script
    reactor.callLater(0.1, reactor.stop)
    defer.returnValue(True)

logging.basicConfig(level=logging.DEBUG)

reactor.callWhenRunning(demo, forecast_id)
reactor.run()
