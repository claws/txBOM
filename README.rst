txBOM
=============

txBOM is a Python Twisted package that allows you to retrieve forecasts and observations
from the Australian Bureau of Meteorology.
Use it to integrate non blocking retrieval of Australian Bureau of Meteorology forecasts
and observations into your Python Twisted application.

**txBOM is currently under development**

Software Dependencies
---------------------

* Python
* Twisted

  - zope.interface
  

Install
=======

1. Download txBOM archive::

    $ git clone git://github.com/claws/txBOM.git
    
For other download options (zip, tarball) visit the github web page of `txCurrentCost <https://github.com/claws/txBOM>`.

2. Install txbom package into your Python distribution::
  
    sudo python setup.py install
    
3. Test::

    $ python
    >>> import txbom
    >>>


Example
=======

Perform a one off retrieval of the current weather forecast for Adelaide::

    from twisted.internet import reactor, defer
    import txbom.forecasts

    # Adelaide forecast identifier
    forecast_id = "IDS10034"
   
    @defer.inlineCallbacks
    def demo(forecast_id):
        
        forecast = yield txbom.forecasts.get_forecast(forecast_id)
        print forecast
        
        # this is the end of the test, stop reactor to finish script
        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)
        
    reactor.callWhenRunning(demo, forecast_id)
    reactor.run()

 
Perform a one off retrieval of weather observations for Adelaide::

    from twisted.internet import reactor, defer
    import logging
    import txbom.observations

    logging.basicConfig(level=logging.DEBUG)

    # Adelaide observations identifier
    observation_url = "http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json"

    @defer.inlineCallbacks
    def demo(observation_url):
        observations = yield txbom.observations.get_observation(observation_url)
        if observations:
            print observations
        else:
            print "No observations?"
        
        # this is the end of the test, stop reactor to finish script
        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)

    reactor.callWhenRunning(demo, observation_url)
    reactor.run()


Use the observations client to maintain up to date observations (use Ctrl+C to exit script)::

    from twisted.internet import reactor
    import txbom.observations

    # Adelaide observations identifier
    observation_url = "http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json"

    def print_current_observation(client):
        if client.observations:
            if client.observations.current:
                print client.observations.current
            else:
                print "No current observation"
        else:
            print "No observations"


    client = txbom.observations.Client(observation_url)

    # strart the client's periodic observations update service.
    reactor.callWhenRunning(client.start)

    # Create a looping call that executes every minute to 
    # print out the client's current observations data.
    # If the script is left to run it should be observed that
    # the client updates its store of observations periodically.
    c = LoopingCall(print_current_observation, client)
    c.start(60)

    reactor.run()
    

        
Todo
====

* Investigate adding locations (State, City) as a separate package so that users don't need to determine
  the forecast identifier or observation url.


