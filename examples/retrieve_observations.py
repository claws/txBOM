#!/usr/bin/env python

'''
A demonstration of a one-off observations retrieval.
'''

from twisted.internet import reactor, defer
import logging
import txbom.observations

logging.basicConfig(level=logging.DEBUG)

# Adelaide observations identifier
observation_url = "http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json"


@defer.inlineCallbacks
def demo(observation_url):
    observations = yield txbom.observations.get_observations(observation_url)
    if observations:
        # observations typically contains many (hundreds, perhaps),
        # lets just print out the current observation.
        print "Current observation data:"
        print observations.current
    else:
        print "No observations retrieved"

    # this is the end of the test, stop reactor to finish script
    reactor.callLater(0.1, reactor.stop)
    defer.returnValue(True)

reactor.callWhenRunning(demo, observation_url)
reactor.run()
