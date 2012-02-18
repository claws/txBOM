#!/usr/bin/env python

'''
Retrieve forecasts from the BOM
'''

import logging
from twisted.protocols.ftp import FTPClient
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.internet import reactor, defer
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO




# Details for the Bureau of Meteorology FTP site
#
BomFtpHost = "ftp2.bom.gov.au"
BomFtpPort = 21
BomFtpForecastPath = "/anon/gen/fwo/%s.txt"



class BufferingProtocol(Protocol):
    """
    Simple utility class that holds all data written to it in a buffer.
    """
    
    def __init__(self):
        self.buffer = StringIO()

    def dataReceived(self, data):
        self.buffer.write(data)
        


@defer.inlineCallbacks
def get_forecast(forecast_id):
    """ 
    Retrieve a text weather forecast from the Australian Bureau of Meteorology FTP 
    server for the city specified by the forecast id.
     
    Returns a deferred to the caller that will eventually return the 
    forecast string.
    
    @param forecast_id: The forecast city identifier. For example Adelaide is
                        IDS10034, Sydney is IDN10064, etc.
    
    @return: A deferred that returns the forecast string or None
    @rtype: defer.Deferred        
    """
    creator = ClientCreator(reactor, FTPClient, username="anonymous", password="guest")
    
    try:
        ftpClient = yield creator.connectTCP(BomFtpHost, BomFtpPort)
    
        bufferProtocol = BufferingProtocol()
        forecast_path = BomFtpForecastPath % (forecast_id)
        result = yield ftpClient.retrieveFile(forecast_path, bufferProtocol)

        forecast = bufferProtocol.buffer.getvalue()
        logging.debug("Got forecast via ftp")
            
        try:
            result = yield ftpClient.quit()
            logging.debug("ftpClient quit successful")
        except Exception, ex:
            logging.error("ftpClient failed to quit properly: %s" % str(ex))
            
        defer.returnValue(forecast)
            
    except Exception, ex:
        logging.error("Connection failed to forecast FTP server: %s" % str(ex))
        defer.returnValue(None)



if __name__ == "__main__":
    
    # test script
    
    # Send Twisted log messages to logging logger
    from twisted.python import log
    observer = log.PythonLoggingObserver()
    observer.start()

    logging.basicConfig(level=logging.DEBUG)


    # Adelaide forecast identifier
    forecast_id = "IDS10034"
    
    @defer.inlineCallbacks
    def demo(forecast_id):
        
        forecast = yield get_forecast(forecast_id)
        print forecast
        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)
        
    reactor.callWhenRunning(demo, forecast_id)
    reactor.run()
    