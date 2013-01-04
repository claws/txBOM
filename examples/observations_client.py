#!/usr/bin/env python

'''
A demonstration of the observations client.

The observations client keeps itself up to date by inspecting
the first observation retrieved and determines the appropriate
time to begin the periodic observations retrieval such that the
minimum number of requests are made to keep the observations
client up to date.

As the observation update rate is 30 minutes this demonstration
can be a little underwhelming to watch. The important point to
understand is that you can create one of these objects and it
will call you back when a new observation has been retrieved,
it does all the work for you.
'''

from twisted.internet import reactor
from twisted.python import log
import logging
import txbom.observations


# Lets implement our own observations client that
# will call us back upon a new observation being
# retrieved.
class MyObservationsClient(txbom.observations.Client):

    def observationsReceived(self, observations):
        '''
        This method receives observation updates as they are retrieved.
        '''
        if self.observations:
            if self.observations.current:
                print "Current observation data:"
                print self.observations.current
            else:
                print "No current observation"
        else:
            print "No observations"


logging.basicConfig(level=logging.DEBUG)

# Send any Twisted log messages to logging logger
_observer = log.PythonLoggingObserver()
_observer.start()

# Adelaide observations identifier
observation_url = "http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json"

client = MyObservationsClient(observation_url)

# strart the client's periodic observations update service.
reactor.callWhenRunning(client.start)
reactor.run()
