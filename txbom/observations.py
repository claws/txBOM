
"""
Retrieve observations from the BOM
"""

import datetime
import logging
import json
from twisted.internet import reactor, defer
from twisted.internet.task import LoopingCall
from twisted.web.client import getPage


#
# Main key in JSON response
#
OBSERVATIONS = 'observations'

#
# main sections in the JSON response
#
NOTICE = 'notice'
HEADER = 'header'
DATA = 'data'

#
# Notice fields in JSON header
#
COPYRIGHT = 'copyright'
COPYRIGHT_URL = 'copyright_url'
DISCLAIMER_URL = 'disclaimer_url'
FEEDBACK_URL = 'feedback_url'

#
# Header fields in JSON header
#
REFRESH_MESSAGE = 'refresh_message'
ID = 'ID'
main_ID = 'main_ID'
NAME = 'name'
STATE_TIME_ZONE = 'state_time_zone'
TIME_ZONE = 'time_zone'
PRODUCT_NAME = 'product_name'
STATE = 'state'

#
# Observation Fields in JSON data
#
AIFSTIME_UTC = 'aifstime_utc'
AIR_TEMP = 'air_temp'
APPARENT_TEMP = 'apparent_t'
CLOUD = 'cloud'
CLOUD_BASE_M = 'cloud_base_m'
CLOUD_OKTAS = 'clound_oktas'
CLOUD_TYPE = 'cloud_type'
CLOUD_TYPE_ID = 'cloud_type_id'
DELTA_TEMP = 'delta_t'
DEW_POINT = 'dewpt'
GUST_KMH = 'gust_kmh'
GUST_KT = 'gust_kt'
HISTORY_PRODUCT = 'history_product'
LAT = 'lat'
LOCAL_DATE_TIME = 'local_date_time'
LOCAL_DATE_TIME_FULL = 'local_date_time_full'
LOCAL_DATE_TIME_WORDED = 'local_date_time_worded'  # manually added
LON = 'lon'
NAME = 'name'
PRESSURE = 'press'
PRESSURE_MSL = 'press_msl'
PRESSURE_QNH = 'press_qnh'
PRESSURE_TEND = 'press_tend'
RAIN_TRACE = 'rain_trace'
RELATIVE_HUMIDITY = 'rel_hum'
SEA_STATE = 'sea_state'
SWELL_DIR_WORDED = 'swell_dir_worded'
SWELL_HEIGHT = 'swell_height'
SWELL_PERIOD = 'swell_period'
VISIBILITY_KMH = 'vis_km'
WEATHER = 'weather'
WIND_DIRECTION = 'wind_dir'
WIND_DIRECTION_WORDED = 'wind_dir_worded'  # manually added
WIND_SPEED_KMH = 'wind_spd_kmh'
WIND_SPEED_KT = 'wind_spd_kt'
WMO = 'wmo'


def validateValue(value):
    """
    Some fields in the returned JSON object contain a value representing
    None. Substitute the Python 'None' for these instances which helps
    later when evaluating whether a field contains actual data.
    """
    if value in ["-", "None"]:
        return None
    return str(value)


class ResponseSection(object):
    """
    A collection of key/value pairs contained within a section of the JSON
    response. The key/value pairs are converted to instance attributes.
    """

    def __init__(self, inDict):
        self.fields = []
        # create instance attributes from each item in the inDict.
        for k, v in inDict.items():
            self.fields.append(str(k))
            setattr(self, str(k), validateValue(v))
        self.fields.sort()

    def __str__(self):
        o = []
        for field in self.fields:
            o.append("%s : %s" % (field, getattr(self, field, None)))
        return "\n".join(o)


class Notice(ResponseSection):
    """
    Notices contained in the Observation response
    """


class Header(ResponseSection):
    """
    Summary information contained in the Observation response
    """


class Observation(ResponseSection):
    """
    A single observation datapoint from the Data section of the response
    """


class Observations(object):
    """
    A Python container for data from the observations response.
    It models the JSON response in that it contains the 3 main sections:

    header
    notice
    data

    header and notice are ResponseSection objects while data holds a
    list of ResponseSection objects for each observation datapoint.

    To access the most recent temperature observation you would access
    the following:
    air_temp = self.data[0].air_temp

    or alternatively using the convenience 'current' property:
    air_temp = self.current.air_temp

    """

    def __init__(self, jsonData):

        noticeDict = jsonData[OBSERVATIONS][NOTICE][0]
        self.notice = Notice(noticeDict)

        headerDict = jsonData[OBSERVATIONS][HEADER][0]
        self.header = Header(headerDict)

        dataDictList = jsonData[OBSERVATIONS][DATA]
        self.data = []
        for dataDict in dataDictList:
            observation = Observation(dataDict)
            self.data.append(observation)

    @property
    def current(self):
        """
        Return the most recent observation datapoint
        """
        if self.data:
            return self.data[0]
        return None

    def __str__(self):
        o = []

        o.append("Header:")
        for field in self.header.fields:
            o.append("\t%s : %s" % (field, getattr(self, field, None)))

        o.append("Notice:")
        for field in self.notice.fields:
            o.append("\t%s : %s" % (field, getattr(self, field, None)))

        totalObservations = len(self.data)
        for i, d in enumerate(self.data):
            o.append("Observation %i of %i:" % (i + 1, totalObservations))
            dStr = "\n".join(["\t%s" % line for line in str(d).split("\n")])
            o.append(dStr)

        return "\n".join(o)


class Client(object):
    """
    The observations client allows a user to obtain BoM observations for a
    specified URL. The client can operate in two modes.

    The first mode simply retrieves the BoM observations whenever the
    Client's get_observations method is called.

    The second mode will keep the client's observations attribute
    up to date by running a periodic task that retrieves the latest observation.
    The update routine used in this mode is optimized to make the fewest
    update requests as possible to maintain current data. It inspects the first
    response and determines the appropriate time to begin the periodic
    observations retrieval such that the minimum number of requests are
    made to keep the observations up to date.
    """

    # Perform an observation retrieval every 30 minutes. This is how often
    # the data is refreshed on the BoM website. There is no point requesting
    # updates any faster.
    Update_Frequency_In_Seconds = 30 * 60

    def __init__(self, observation_url=None):
        self.observation_url = observation_url

        # The most recent observation response object
        self.observations = None

        # A reference to the task that periodically requests an
        # observation update. This is needed so the task can be
        # stopped later.
        self.periodicRetrievalTask = None

    def start(self):
        """
        Start monitoring sensors in and around the home environment
        """
        if self.observation_url is None:
            logging.error("Can't start periodic observations retrieval as no URL is set")
            return

        logging.info('BoM Observation Client starting')
        # Obtain the first observation right now. Inspect the update timestamp
        # attribute so we can determine the time until the next update which
        # will determine the time at which the periodic update task will begin.
        #
        self.retrieveFirstObservations()

    def stop(self):
        """
        Stop monitoring sensors in and around the home environment
        """
        logging.info('BoM Observation Client stopping')

        if self.periodicRetrievalTask:
            self.periodicRetrievalTask.stop()
            self.periodicRetrievalTask = None

    @defer.inlineCallbacks
    def retrieveFirstObservations(self):
        """
        Retrieve the first BOM observations and inspect it for the most recent
        update time. Using that information determine the time until the next
        observation update and schedule the BOM retrieval task to begin running
        periodically at the calculated delay interval.
        """
        try:
            observations = yield self.get_observations(self.observation_url)
            self.observations = observations

            self.observationsReceived(observations)

            if observations.current.aifstime_utc:
                refresh_utc = datetime.datetime.strptime(observations.current.aifstime_utc, "%Y%m%d%H%M%S")
                # While the update timestamp within the data indicates an update interval
                # of 30 minutes, the updates of the half hourly data at the BoM web site
                # seem to occur at 5 minutes past the data timestamp so the real time to
                # the next update is 30 minutes (for the data) + 5 minutes (for the web
                # server to receive the data update). Then I'll add 2 minutes of buffer
                # time to ensure that the next query will see new data.
                # Therefore the total time from the last data timestamp to the next query
                # will be 30 + 5 + 2 = 37 minutes. From that initial offset time the
                # periodic task runs at intervals of Update_Frequency_In_Seconds seconds.
                next_refresh_time = refresh_utc + datetime.timedelta(minutes=37)
                now_utc = datetime.datetime.utcnow()
                time_until_next_refresh = next_refresh_time - now_utc
                logging.info("Scheduling the periodic observation retrieval task to begin after delay of: %s" % time_until_next_refresh)
                delay_in_seconds = time_until_next_refresh.total_seconds()
                reactor.callLater(delay_in_seconds, self.startPeriodicRetrievalTask)
            else:
                logging.error("Could not extract most recent BOM refresh time from %s field" % AIFSTIME_UTC)

        except Exception, ex:
            logging.error("First BoM observation retrieval failed")
            logging.exception(ex)
            # schedule another attempt in 10 seconds.
            logging.info("Scheduling another attempt to retrieve first BoM observation")
            reactor.callLater(10, self.retrieveFirstObservations)

        defer.returnValue(True)

    def startPeriodicRetrievalTask(self):
        """
        Begin the looping call that will retrieve the latest BoM observation
        """
        self.bomUpdateTask = LoopingCall(self._retrieveObservations)
        self.bomUpdateTask.start(Client.Update_Frequency_In_Seconds, now=True)
        logging.info("Starting periodic BoM observation retrieval task")

    @defer.inlineCallbacks
    def _retrieveObservations(self):
        """
        Retrieve the latest BoM observation and store it
        """
        observations = yield self.get_observations(self.observation_url)
        if observations:
            logging.info("BoM observations retrieved successfully")
            self.observations = observations

            # pass observations off the user provided handler
            self.observationsReceived(observations)

        defer.returnValue(None)

    @defer.inlineCallbacks
    def get_observations(self, observation_url):
        """
        Retrieve the latest observations from the BOM in JSON format.

        Returns a deferred that will eventually return an Observation
        object with attributes populated from parsing the JSON update.

        @return: A deferred that returns an Observations object
        @rtype: defer.Deferred
        """
        try:
            logging.debug("Requesting new observation data from: %s" % observation_url)
            jsonString = yield getPage(observation_url)
            logging.debug("Retrieved new observation data")
            jsonData = json.loads(jsonString)
            observations = Observations(jsonData)
            defer.returnValue(observations)
        except Exception, ex:
            logging.error("Unable to retrieve observations data:")
            logging.exception(ex)
            defer.returnValue(None)

    def observationsReceived(self, observations):
        """
        Override this method to receive observation updates as they are
        retrieved.
        """
        pass


def get_observations(observation_url):
    """
    Retrieve the latest observations from the BOM.
    Returns a deferred to the caller that will eventually return a
    Observations object or None.

    @return: A deferred that returns a Observations object
    @rtype: defer.Deferred
    """
    logging.debug("Retrieving observations from url %s" % (observation_url))
    return Client().get_observations(observation_url)
