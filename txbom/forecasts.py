#!/usr/bin/env python

'''
Retrieve forecasts from the BOM
'''

import logging
from twisted.protocols.ftp import FTPClient
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.internet import reactor, defer
import txbom
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


# Details for the Bureau of Meteorology FTP site
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
        _result = yield ftpClient.retrieveFile(forecast_path, bufferProtocol)

        forecast = bufferProtocol.buffer.getvalue()
        forecast = forecast.replace("\r", "")  # prefer \n as line delimiters
        logging.debug("Forecast retrieval successful")

        try:
            _result = yield ftpClient.quit()
        except Exception, ex:
            logging.error("ftpClient failed to quit properly")
            logging.exception(ex)

        defer.returnValue(forecast)

    except Exception, ex:
        logging.error("Connection to forecast FTP server failed")
        logging.exception(ex)
        defer.returnValue(None)


def expand_contractions(data):
    """
    Return a string with expanded full words for typical
    contractions used in forecast reports. This can be
    useful if the forecast will be sent through text to
    speech.
    """
    contractions = {"N'ly": "northerly",
                    "S'ly": "southerly",
                    "E'ly": "easterly",
                    "W'ly": "westerly"}
    for contraction, replacement in contractions.items():
        data = data.replace(contraction, replacement)

    # change 'km/h' to 'kilometers per hour'
    data = data.replace("km/h", "kilometers per hour")

    # change 'S/SE' to 'S to SE'
    tmp = []
    for d in data.split(" "):
        if "/" in d:
            before, after = d.split("/")
            if before in txbom.WindDirections and after in txbom.WindDirections:
                d = "%s to %s" % (before, after)
        tmp.append(d)
    data = " ".join(tmp)

    # Convert ' S ' to ' southerly '
    # Process wind direction keys from longest to shortest so that
    # we don't get 'northerlyeasterly' from NE. Instead we should end
    # up with 'north easterly'.
    keys = txbom.WindDirections.keys()
    keys.sort(key=len)
    keys.reverse()
    for k in keys:
        v = txbom.WindDirections[k]
        replace_str = " %s " % k
        sub_str = " %s " % v
        data = data.replace(replace_str, sub_str)

    return data


def get_summary_information(data):
    """
    Return a tuple of summary data extracted from the forecast string.
    The tuple returned contains 5 items, identifier, location, state
    time, date.
    """

    chunks = data.split("\n\n")
    forecast_header = chunks[0]
    forecast_info = chunks[1]

    theId = forecast_header.split("\n")[0].strip()
    theState = forecast_header.split("\n")[-1].strip()

    theLocation = forecast_info.split("\n")[0]
    theLocation = " ".join(theLocation.split()[:-1])
    theLocation = theLocation.replace("Updated ", "")
    theLocation = theLocation.replace(" Metropolitan Area", "")
    time = forecast_info.split("\n")[1]
    items = time.split()
    theTime = " ".join(items[2:4])
    theDate = " ".join(items[6:])

    return (theId, theLocation, theState, theTime, theDate)


def get_warnings_information(data):
    """
    Return a string containing warnings found in the forecast data
    """
    # Warnings typically look like this..
    #
    # Warning Summary at issue time
    # Nil.
    # Details of warnings are available on the Bureau's website www.bom.gov.au, by
    # telephone 1300-659-218* or through some TV and radio broadcasts.
    #
    # or this...
    #
    # Warning Summary
    # Nil.
    #
    warnings = None
    for chunk in data.split("\n\n"):
        if chunk.startswith("Warning Summary"):
            warningLines = chunk.split("\n")[1:]
            for non_warning_item in ['Nil', 'Details of', 'telephone']:
                index = None
                for i, line in enumerate(warningLines):
                    if line.startswith(non_warning_item):
                        index = i
                        break

                # remove non warning line if it was found
                if index is not None:
                    del warningLines[index]

            if warningLines:
                warnings = " ".join(warningLines)

            break

    return warnings


def get_uv_information(data):
    """
    Return a 3 tuple containing the uv_alert time span, the
    uv_index value and the uv index name.
    """
    uv_alert, uv_index, uv_index_name = None, None, None
    for line in data.split("\n"):
        if "UV Alert" in line:
            uv_alert_data, uv_index_data = line.split("UV Index predicted to reach ")

            # get the UV alert time span
            if "No UV Alert" not in uv_alert_data:
                uv_alert_data = uv_alert_data.replace("UV Alert from ", "")
                uv_alert_data = uv_alert_data.replace("UV Alert:", "")
                uv_alert_data = uv_alert_data.strip()
                if uv_alert_data.endswith(","):
                    uv_alert_data = uv_alert_data[:-1]
                uv_alert = uv_alert_data.strip()

            # get the expect UV index
            uv_index, uv_index_name = uv_index_data.strip().split(" [")
            uv_index = uv_index.strip()
            uv_index_name = uv_index_name.replace("]", "")

            break

    return (uv_alert, uv_index, uv_index_name)


def get_forecast_for_today(data):
    """
    Return a tuple containing description, precis, temperature min and
    temperature max forecast data for for tomorrow if it can be found
    in the forecast string.
    """
    description, content, temperature = None, None, None

    today_forecast_index = None
    chunks = data.split("\n\n")
    for i, chunk in enumerate(chunks):
        if chunk.startswith("Forecast for "):
            today_forecast_index = i
            break

    if today_forecast_index:
        today_forecast = chunks[today_forecast_index]

        description = today_forecast.split("\n", 1)[0]
        description = description.replace("Forecast for ", "")
        description = description.replace("the rest of ", "")
        description = description.strip()

        items = today_forecast.split("\n")[1:]

        if len(items) > 1:
            content = " ".join(items)
        else:
            content = items[0]

        content = expand_contractions(content)

        today_details = chunks[today_forecast_index + 1]

        if today_details.startswith('Precis'):
            lines = today_details.split("\n")
            precis_line = lines[0]

            if precis_line.startswith("Precis"):
                precis = precis_line.replace("Precis", "")
                precis = precis.replace(":", "")
                precis = precis.strip()
                if precis.endswith("."):
                    precis = precis[:-1]

            # temp typically follows the precis line, but not always
            if len(lines) > 1:
                temp_line = lines[1]
                # temp appears to alway be last item on line
                temp_line = temp_line.strip()
                temperature = temp_line.split()[-1]

        else:
            # details should be on one line
            today_details = today_details.split("\n")[0]
            items = today_details.split("  ")
            items = filter(None, items)  # remove empty items

            if len(items) == 3:
                location, precis, temperature = items

                precis = precis.strip()
                if precis.endswith("."):
                    precis = precis[:-1]

                temperature = temperature.replace("Max", "")
                temperature = temperature.strip()

            elif len(items) == 2:
                location, precis = items

                precis = precis.strip()
                if precis.endswith("."):
                    precis = precis[:-1]

    return (description, content, precis, temperature)


def get_forecast_for_tomorrow(data):
    """
    Return a tuple containing description, precis, temperature min and
    temperature max forecast data for for tomorrow if it can be found
    in the forecast string.
    """
    description = None
    precis = None
    temperature_min = None
    temperature_max = None

    forecasts = []
    chunks = data.split("\n\n")
    for i, chunk in enumerate(chunks):
        if chunk.startswith("Forecast for "):
            forecasts.append(i)

    TwoForecastsPresent = len(forecasts) > 1

    if TwoForecastsPresent:

        # typically the forecast for tomorrow spans two chunks. The first
        # contains the description and the second contains the precis and
        # temperature.
        tomorrow_forecast_index = forecasts[1]
        tomorrowsForecast = chunks[tomorrow_forecast_index]

        description = tomorrowsForecast.split("\n", 1)[0]
        description = description.replace("Forecast for ", "")
        description = description.strip()

        content = tomorrowsForecast.split("\n")[1]
        content = content.strip()
        # prefer the longer description over the shorter precis
        precis = content

        # the temperatures for tomorrow's forecast appears to always be in
        # the following block.
        tomorrow_details = chunks[tomorrow_forecast_index + 1]

        if tomorrow_details.startswith('Precis'):
            lines = tomorrow_details.split("\n")
            precis_line = lines[0]

            if precis_line.startswith("Precis"):
                precis = precis_line.replace("Precis", "")
                precis = precis.replace(":", "")
                precis = precis.strip()
                if precis.endswith("."):
                    precis = precis[:-1]

            # temp typically follows the precis line, but not always
            if len(lines) > 1:
                temp_line = lines[1]
                items = temp_line.split("  ")
                items = filter(None, items)  # remove empty items

                if len(items) == 3:
                    _, temperature_min, temperature_max = items
                elif len(items) == 2:
                    _, temperature_max = items

                if temperature_min:
                    temperature_min = temperature_min.replace("Min", "")
                    temperature_min = temperature_min.strip()

                if temperature_max:
                    temperature_max = temperature_max.replace("Max", "")
                    temperature_max = temperature_max.strip()
                # temp appears to alway be last item on line
                temp_line = temp_line.strip()
                _temperature = temp_line.split()[-1]

        else:

            forecast_line = tomorrow_details.split("\n")[0]
            items = forecast_line.split("  ")
            items = filter(None, items)  # remove empty items
            try:
                location, _, temperature_min, temperature_max = items

                temperature_min = temperature_min.replace("Min", "")
                temperature_min = temperature_min.strip()

                temperature_max = temperature_max.replace("Max", "")
                temperature_max = temperature_max.strip()

            except ValueError, ex:
                logging.error("Error extracting 4 items from line: \'%s\'. items=%s" % (forecast_line, str(items)))
                logging.exception(ex)

    else:
        # try one of the other formats which looks like this:
        # Sunday           Fine, partly cloudy.                  Min 12   Max 24
        # Monday           A few showers.                        Min 13   Max 23
        # Tuesday          A few showers.                        Min 14   Max 23
        # Wednesday        A few showers.                        Min 13   Max 24
        # Thursday         A few showers.                        Min 15   Max 25
        # Friday           Showers.
        #
        # This block format seems to always follow the UV Alert block
        tomorrow_forecast_index = None
        for i, chunk in enumerate(chunks):
            # typically the chunk starts with UV Alert but sometimes it
            # can be bunched up with the chunk before.
            if "UV Alert" in chunk:
                tomorrow_forecast_index = i + 1
                break

        if tomorrow_forecast_index is not None:
            tomorrowsForecast = chunks[tomorrow_forecast_index]
            forecast_line = tomorrowsForecast.split("\n")[0]

            items = forecast_line.split("  ")
            items = filter(None, items)  # remove empty items
            description, precis, temperature_min, temperature_max = items

            description = description.strip()

            precis = precis.strip()
            if precis.endswith("."):
                precis = precis[:-1]

            temperature_min = temperature_min.replace("Min", "")
            temperature_min = temperature_min.strip()

            temperature_max = temperature_max.replace("Max", "")
            temperature_max = temperature_max.strip()

    return (description, precis, temperature_min, temperature_max)


def get_five_day_forecast(data):
    """
    Return a list of tuples containing forecast information for the next
    five days.  There are a few ways that 5 day forecasts can be presented.
    """
    nextFiveDays = []

    forecasts = []
    chunks = data.split("\n\n")
    for i, chunk in enumerate(chunks):
        if chunk.startswith("Forecast for "):
            forecasts.append(i)

    FiveForecastsPresent = len(forecasts) > 5

    if FiveForecastsPresent:
        FiveForcasts = forecasts[-5:]
        for index in FiveForcasts:

            forecast_line = chunks[index]
            day_name = forecast_line.split("\n")[0]
            day_name = day_name.replace("Forecast for ", "")
            day_name = day_name.strip()

            # The short form forecast details are typically in the
            # following chunk from the long forecast.
            chunk = chunks[index + 1]
            forecast_line = chunk.split("\n", 1)[0]

            items = forecast_line.split("  ")
            items = filter(None, items)  # remove empty items

            if len(items) == 3:
                # occasionally the precis and min temp are not separated
                # by a space. Eg. Sunny.Min 9
                _, precis_and_min, temperature_max = items
                precis, temperature_min = precis_and_min.rsplit(".", 1)
            else:
                _, precis, temperature_min, temperature_max = items

            precis = precis.strip()
            if precis.endswith("."):
                precis = precis[:-1]

            temperature_min = temperature_min.replace("Min", "")
            temperature_min = temperature_min.strip()

            temperature_max = temperature_max.replace("Max", "")
            temperature_max = temperature_max.strip()

            nextFiveDays.append((day_name, temperature_min, temperature_max, precis))

    else:
        # try one of the other formats which looks like this:
        # Sunday           Fine, partly cloudy.                  Min 12   Max 24
        # Monday           A few showers.                        Min 13   Max 23
        # Tuesday          A few showers.                        Min 14   Max 23
        # Wednesday        A few showers.                        Min 13   Max 24
        # Thursday         A few showers.                        Min 15   Max 25
        # Friday           Showers.
        #
        # This block format seems to always follow the UV Alert block
        five_day_forecast_candidate_index = None
        for i, chunk in enumerate(chunks):
            # typically the chunk starts with UV Alert but sometimes it
            # can be bunched up with the chunk before.
            if "UV Alert" in chunk:
                five_day_forecast_candidate_index = i + 1
                break

        if five_day_forecast_candidate_index is not None:

            # sometimes there can be the second day's forecasts after the UV Alert
            # which is then followed by the five day forecast. Crazy!
            five_day_forecast = chunks[five_day_forecast_candidate_index]
            if five_day_forecast.startswith("Forecast for "):
                # skip this and the next chunk
                five_day_forecast = chunks[five_day_forecast_candidate_index + 2]

            forecast_lines = five_day_forecast.split("\n")
            for forecast_line in forecast_lines:
                items = forecast_line.split("  ")
                items = filter(None, items)  # remove empty items
                day_name, precis, temperature_min, temperature_max = items

                day_name = day_name.strip()

                precis = precis.strip()
                if precis.endswith("."):
                    precis = precis[:-1]

                temperature_min = temperature_min.replace("Min", "")
                temperature_min = temperature_min.strip()

                temperature_max = temperature_max.replace("Max", "")
                temperature_max = temperature_max.strip()

                nextFiveDays.append((day_name, temperature_min, temperature_max, precis))

    return nextFiveDays


def forecastToDict(forecast=None):
    """
    Extract as much information as possible from the forecast text
    and return it in a dict format with unique keys. This format
    can be useful in string.Template substitutions when building
    you own forecast format.
    """
    if forecast:

        # remove whitespace from whitespace-only lines, leaving just the newline char
        forecast = "\n".join([line.strip() for line in forecast.split("\n")])

        # extract summary information
        theId, theLocation, theState, theTime, theDate = get_summary_information(forecast)

        # Extract any warnings
        warnings = get_warnings_information(forecast)

        # extract today's forecast
        today_description, today_content, today_precis, today_temperature = get_forecast_for_today(forecast)

        # extract tomorrow's forecast if it can be found
        tomorrow_description, tomorrow_precis, tomorrow_min, tomorrow_max = get_forecast_for_tomorrow(forecast)

        # Attempt to extract a 5 day forecast if one is present
        next_five_days = get_five_day_forecast(forecast)

        # Attempt to extract UV Alert information
        uv_alert, uv_index, uv_index_name = get_uv_information(forecast)

        forecastDict = {"fcast_id": theId,
                        "fcast_town": theLocation,
                        "fcast_state": theState,
                        "fcast_date": theDate,
                        "fcast_time": theTime,
                        "fcast_warnings": warnings,
                        "fcast_uv_alert": uv_alert,
                        "fcast_uv_index": uv_index,
                        "fcast_uv_index_name": uv_index_name,
                        "fcast_today": today_description,
                        "fcast_today_content": today_content,
                        "fcast_today_precis": today_precis,
                        "fcast_today_temperature": today_temperature,
                        "fcast_tomorrow": tomorrow_description,
                        "fcast_tomorrow_precis": tomorrow_precis,
                        "fcast_tomorrow_minimum": tomorrow_min,
                        "fcast_tomorrow_maximum": tomorrow_max,
                        "fcast_five_days": next_five_days,
                        "fcast_raw": forecast}

        return forecastDict

    else:
        logging.error("Invalid forecast string received, can't produce dict.")
        return None
