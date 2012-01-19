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

2. Install txBOM module into your Python distribution::
  
    sudo python setup.py install
    
3. Test::

    $ python
    >>> import txBOM
    >>>


Example
=======

Retrieve the forecast for Adelaide::

    from twisted.internet import reactor
    import logging
    import txBOM.forecasts

    logging.basicConfig(level=logging.DEBUG)

    # Adelaide forecast identifier
    forecast_id = "IDS10034"
    
    def begin(forecast_id):
        
        def print_forecast(forecast):
            print forecast
            return True
        
        def shutdown(result):
            # Allow a second for ftp quit to complete.
            reactor.callLater(1.0, reactor.stop)
            
        d = txBOM.forecasts.get_forecast(forecast_id)
        d.addCallback(print_forecast)
        d.addCallback(shutdown)
        
    reactor.callWhenRunning(begin, forecast_id)
    reactor.run()


Retrieve the latest observations for Adelaide::

    from twisted.internet import reactor
    import logging
    import txBOM.observations

    logging.basicConfig(level=logging.DEBUG)

    # Adelaide observations identifier
    observation_url = "http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json"

    def print_observation(observations):
        if observations.current:
            print observations.current
        else:
            print "No current observation"

        # this is the end of the test, stop reactor to finish script
        reactor.callLater(1.0, reactor.stop)

    d = txBOM.observations.get_observation(observation_url)
    d.addCallback(print_observation)
    reactor.run()



Use the observations client to maintain up to date observations::

    from twisted.internet import reactor
    import logging
    import txBOM.observations

    logging.basicConfig(level=logging.DEBUG)

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

    client = Client(observation_url)
    reactor.callWhenRunning(client.start)
    c = LoopingCall(print_current_observation, client)
    c.start(60)
    reactor.run()
    

        
Todo
====

* N/A


