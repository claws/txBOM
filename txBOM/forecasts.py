
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
        



def get_forecast(forecast_id):
    """ 
    Retrieve a text weather forecast from the Australian Bureau of Meteorology FTP server
    for the city
     
    Returns a deferred to the caller that will eventually return the 
    forecast string.
    
    @param forecast_id: The forecast city identifier. For example Adelaide is
                        IDS10034, Sydney is IDN10064, etc.
    
    @return: A deferred that returns the forecast string
    @rtype: defer.Deferred        
    """

    def connectionMade(ftpClient, path, deferred):
        """ Retrieve forecast file now that FTP server connection is established """
    
        def retrievalSuccess(result, ftpClient, bufferProtocol, deferred):
            """ Forecast retrieval was successful """
            def onFtpClientQuitSuccess(ignored):
                logging.debug("ftpClient quit successful")
            def onFtpClientQuitFailed(failure):
                logging.error("ftpClient failed to quit properly: %s" % str(failure))
                
            d = ftpClient.quit()
            d.addCallback(onFtpClientQuitSuccess)
            d.addErrback(onFtpClientQuitFailed)
            
            # pass forecast data back to caller
            forecast = bufferProtocol.buffer.getvalue()
            logging.debug("Got forecast via ftp")
            deferred.callback(forecast)
        
        def retrievalFailed(failure):
            """ Forecast retrieval was unsuccessful """
            logging.error("Forecast file retrieval failed: %s" % str(failure))
        
        
        bufferProtocol = BufferingProtocol()
        d = ftpClient.retrieveFile(path, bufferProtocol)
        d.addCallback(retrievalSuccess, ftpClient, bufferProtocol, deferred)
        d.addErrback(retrievalFailed)
    
    
    def connectionFailed(reason):
        """ Forecast FTP server connection failed """
        logging.error("Connection failed to forecast FTP server: %s" % str(reason))


    forecast_path = BomFtpForecastPath % (forecast_id)
    creator = ClientCreator(reactor, FTPClient, username="anonymous", password="guest")
    
    deferred = defer.Deferred()
    d = creator.connectTCP(BomFtpHost, BomFtpPort)
    d.addCallback(connectionMade, forecast_path, deferred)
    d.addErrback(connectionFailed)
    
    return deferred



if __name__ == "__main__":
    
    # test script
    
    # Send Twisted log messages to logging logger
    from twisted.python import log
    observer = log.PythonLoggingObserver()
    observer.start()

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
            
        d = get_forecast(forecast_id)
        d.addCallback(print_forecast)
        d.addCallback(shutdown)
        
    reactor.callWhenRunning(begin, forecast_id)
    reactor.run()
    