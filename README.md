# txBOM

txBOM is a Python Twisted package that lets you retrieve forecasts and observations from the Australian Bureau of Meteorology (BOM).

Use it to integrate non blocking retrieval of Australian Bureau of Meteorology forecasts and observations into your Python Twisted application.


## Software Dependencies

* Python
* Twisted

  - zope.interface


## Install

A number of methods are available to install this package.

* Using pip with PyPI as source:

```bash
$ [sudo] pip install txbom
```

* Using pip with github source:

```bash
$ [sudo] pip install git+git://github.com/claws/txBOM.git
```

* Manually download and install the txBOM archive. For other manual download options (zip, tarball) visit the github web page of [txBOM](https://github.com/claws/txBOM):

```bash
$ git clone git://github.com/claws/txBOM.git
$ cd txBOM
$ [sudo] python setup.py install
```

### Test Installation

```bash
$ python
>>> import txbom
>>>
```

## Examples

Examples scripts can be found in the examples directory. From the examples directory the following scripts can be run (assuming the txbom package is installed or can be found using the PYTHONPATH):

### Retrieve Forecast
This script demonstrates how to retrieve a forecast and also how the forecast can be parsed into a useful dict.

```bash
$ python retrieve_forecast.py
```

Example output:
```python
DEBUG:root:Forecast retrieval successful
Received forecast text:
IDS10034
Australian Government Bureau of Meteorology
South Australia

Adelaide Forecast
Issued at 5:20 am CDT on Friday 4 January 2013
for the period until midnight CDT Thursday 10 January 2013.

Warning Summary at issue time
Fire Weather Warning for the Adelaide Metropolitan forecast district for Friday.
Details of warnings are available on the Bureau's website www.bom.gov.au, by
telephone 1300-659-215* or through some TV and radio broadcasts.

Forecast for the rest of Friday 4 January
Sunny. Very hot. Winds northeast to northwesterly 25 to 40 km/h tending west to
northwesterly 20 to 30 km/h in the early afternoon ahead of milder south to
southwesterly 20 to 30 km/h late afternoon or evening.

City Centre         Sunny. Evening milder change. Max 44  
Chance of any rainfall: 0%            
Rainfall: 0 mm                
<raw forecast text truncated for brevity>

Forecast dict:
fcast_date : Friday 4 January 2013
fcast_five_days : [('Sunday 6 January', '17', '36', 'Sunny'), ('Monday 7 January', '22', '41', 'Sunny'), ('Tuesday 8 January', '22', '38', 'Sunny'), ('Wednesday 9 January', '18', '37', 'Mostly sunny'), ('Thursday 10 January', '18', '36', 'Sunny')]
fcast_id : IDS10034
fcast_raw : <raw forecast text truncated for brevity>
fcast_state : South Australia
fcast_time : 5:20 am
fcast_today : Friday 4 January
fcast_today_content : Sunny. Very hot. Winds northeast to northwesterly 25 to 40 kilometers per hour tending west to northwesterly 20 to 30 kilometers per hour in the early afternoon ahead of milder south to southwesterly 20 to 30 kilometers per hour late afternoon or evening.
fcast_today_precis : Sunny. Evening milder change. Max 44
fcast_today_temperature : None
fcast_tomorrow : Saturday 5 January
fcast_tomorrow_maximum : 31
fcast_tomorrow_minimum : 17
fcast_tomorrow_precis : Sunny. Winds south to southeasterly 20 to 30 km/h, reaching 40 km/h about the
fcast_town : Adelaide
fcast_uv_alert : 9:10 am to 5:40 pm
fcast_uv_index : 13
fcast_uv_index_name : Extreme
fcast_warnings : Fire Weather Warning for the Adelaide Metropolitan forecast district for Friday.
```

### Retrieve Observations
This script demonstrates how to use txbom to retrieve weather observations. Weather observations are published to the BOM site approximately every half hour. Using this approach you would need to manage how often you retrieve the observations to keep them current.

```bash
$ python retrieve_observations.py
```

Example output:
```python
DEBUG:root:Retrieving observations from url http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json
DEBUG:root:Requesting new observation data from: http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json
DEBUG:root:Retrieved new observation data
Current observation data:
aifstime_utc : 20130104043000
air_temp : 44.3
apparent_t : 37.6
cloud : None
cloud_base_m : None
cloud_oktas : None
cloud_type : None
cloud_type_id : None
delta_t : 24.0
dewpt : -4.5
gust_kmh : 35
gust_kt : 19
history_product : IDS60901
lat : -34.9
local_date_time : 04/03:00pm
local_date_time_full : 20130104150000
lon : 138.6
name : Adelaide
press : 1002.8
press_msl : 1002.8
press_qnh : 1002.9
press_tend : None
rain_trace : 0.0
rel_hum : 5
sea_state : None
sort_order : 0
swell_dir_worded : None
swell_height : None
swell_period : None
vis_km : None
weather : None
wind_dir : NW
wind_spd_kmh : 22
wind_spd_kt : 12
wmo : 94675
```

### Use the observations client to maintain up to date observations

This example demonstrates how to use the txbom observations client to automatically keep weather observations up to date.

The observations client keeps itself up to date by inspecting the first observation retrieved and determines the appropriate time to begin the periodic observations retrieval such that the minimum number of requests are made to keep the observations client up to date.

As the observation update rate is 30 minutes this demonstration can be a little underwhelming to watch. The important point to understand is that you can create one of these objects and it will call you back when a new observation has been retrieved, it does all the work for you.

Ctrl+C will exit this long running script:
```bash
$ python observations_client.py
```

Example output:
```python
INFO:root:BoM Observation Client starting
DEBUG:root:Requesting new observation data from: http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json
INFO:twisted:Starting factory <HTTPClientFactory: http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json>
DEBUG:root:Retrieved new observation data
Current observation data:
aifstime_utc : 20130104050000
air_temp : 44.0
apparent_t : 37.1
cloud : None
cloud_base_m : None
cloud_oktas : None
cloud_type : None
cloud_type_id : None
delta_t : 24.0
dewpt : -5.9
gust_kmh : 30
gust_kt : 16
history_product : IDS60901
lat : -34.9
local_date_time : 04/03:30pm
local_date_time_full : 20130104153000
lon : 138.6
name : Adelaide
press : 1002.7
press_msl : None
press_qnh : 1002.7
press_tend : None
rain_trace : 0.0
rel_hum : 4
sea_state : None
sort_order : 0
swell_dir_worded : None
swell_height : None
swell_period : None
vis_km : None
weather : None
wind_dir : NW
wind_spd_kmh : 22
wind_spd_kt : 12
wmo : 94675
INFO:root:Scheduling the periodic observation retrieval task to begin after delay of: 0:08:58.307281
INFO:twisted:Stopping factory <HTTPClientFactory: http://www.bom.gov.au/fwo/IDS60901/IDS60901.94675.json>
```

## Todo

* Investigate adding locations (State, City) as a separate package so that users don't need to determine the forecast identifier or observation url.


