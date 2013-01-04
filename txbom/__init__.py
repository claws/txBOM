
'''
txBOM lets you integrate asynchronous weather forecast and
observations retrieval from the Australian Bureau of Meteorology
into your Twisted application.

Data definitions extracted from http://www.bom.gov.au/inside/itb/dm/idcodes/struc.shtml
'''


version = (0, 0, 2)


# General form of the ID Code
#
# The general form of the identification code is:
#
# IDcxxxxx.ext
#
# where:
#  ID = a constant which identifies this string as an ID code;
#  c = category of product
#  xxxxx = individual product identifier whose form depends on the category, c;
#  ext = optional file extension, indicating file type
#
# Category of product (idCxxxxx)  may have the following values:
#
# B = Bundled products, eg IDBxxxxx
# C = Climate, eg IDCxxxxx
# D = NT, eg IDDxxxxx
# E = Satellite products, eg IDExxxxx
# G = Graphical Weather Packages, eg IDGxxxxx
# N = NSW/ACT, eg IDNxxxxx
# Q = Qld, eg IDQxxxxx
# R = Radar, eg IDRxxxxx
# S = SA, eg IDSxxxxx
# T = Tasmanian products, eg IDTxxxxx
# V = Victoria, eg IDVxxxxx
# W = WA, eg IDWxxxxx
# X = Digital Fax, eg IDXxxxxx
# Y = National Meteorological Operations Centre, eg IDYxxxxx
#
ACT = "N"   # e.g. IDNxxxxx
Bundled = "B"
Climate = "C"
NT = "D"   # e.g. IDDxxxxx
Satellite = "E"
Graphical = "G"
NSW = "N"   # e.g. IDNxxxxx
QLD = "Q"   # e.g. IDQxxxxx
Radar = "R"
SA = "S"   # e.g. IDSxxxxx
TAS = "T"   # e.g. IDTxxxxx
VIC = "V"   # e.g. IDVxxxxx
WA = "W"   # e.g. IDWxxxxx
Digital_Fax = "X"
National_Operations_Centre = "Y"

Categories = [ACT,
              Bundled,
              Climate,
              NT,
              Satellite,
              Graphical,
              NSW,
              QLD,
              Radar,
              SA,
              TAS,
              VIC,
              WA,
              Digital_Fax,
              National_Operations_Centre]

StateCategories = [ACT,
                   NSW,
                   NT,
                   QLD,
                   SA,
                   TAS,
                   VIC,
                   WA]

# Individual product identifier (idcXXXXX)
#
# The identifier field varies in length and composition, depending upon the category of product - c.
# For full details, refer to the Product Identification Code Listing.
#
# Optional file extension (idcxxxxx.EXT)
#
# The file extension is optional. When required it indicates the product's file type or format as follows:
#
# .au = voice file
# .axf = AIFS Exchange Format file
# .cat = concatenated voice file
# .gif = gif image file
# .htm = html/shtml file
# .jpg = jpeg image file
# .mpg = mpeg image file
# .nc = NetCDF file
# .ps = postscript
# .txt = text file
# .wav = voice file


# Convert wind direction acronym to words
WindDirections = {"N": "northerly",
                  "NNE": "north north easterly",
                  "NE": "north easterly",
                  "ENE": "east north easterly",
                  "E": "easterly",
                  "ESE": "east south easterly",
                  "SE": "south easterly",
                  "SSE": "south south easterly",
                  "S": "southerly",
                  "SSW": "south south westerly",
                  "SW": "south westerly",
                  "WSW": "west south westerly",
                  "W": "westerly",
                  "WNW": "west north westerly",
                  "NW": "north westerly",
                  "NNW": "north north westerly",
                  "CALM": "calm"}

WindDirectionsToBearing = {"N": 90.0,
                           "NNE": 67.5,
                           "NE": 45.0,
                           "ENE": 22.5,
                           "E": 0.0,
                           "ESE": 337.5,
                           "SE": 315,
                           "SSE": 292.5,
                           "S": 270.0,
                           "SSW": 247.5,
                           "SW": 225.0,
                           "WSW": 202.5,
                           "W": 180.0,
                           "WNW": 157.5,
                           "NW": 135.0,
                           "NNW": 112.5,
                           "CALM": None}

