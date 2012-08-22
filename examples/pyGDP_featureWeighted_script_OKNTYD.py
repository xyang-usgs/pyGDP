import pyGDP
import numpy as np
import matplotlib.dates as mdates

pyGDP = pyGDP.pyGDPwebProcessing()


filePath = 'testUpload.zip'
#upload the file to geoserver
shpfile = pyGDP.uploadShapeFile(filePath)

print 
shapefiles = pyGDP.getShapefiles()
print 'Available shapefiles: '
for shapefile in shapefiles:
    print shapefile
 
# Grab the file and get its attributes:
OKshapefile = shpfile
if OKshapefile not in shapefiles:
    print str(shpfile) + ' not on server.'
    exit()

attributes = pyGDP.getAttributes(OKshapefile)
for attr in attributes:
    print attr

# Grab the values from 'OBJECTID' and 'upload:OKCNTYD'
usr_attribute = 'OBJECTID'
values = pyGDP.getValues(OKshapefile, usr_attribute)
for v in values:
    print v

#We set our value to 13
usr_value = 13

# our shapefile = 'upload:OKCNTYD', usr_attribute = 'OBJECTID', and usr_value = 13
# We get the dataset URI that we are interested in
dataSetURIs = pyGDP.getDataSetURI()
for d in dataSetURIs:
    print d

# Set our datasetURI
dataSetURI = 'dods://cida.usgs.gov/qa/thredds/dodsC/prism'
# Get the available data types associated with the dataset
dataType = 'ppt'
# Get available time range on the dataset
timeRange = pyGDP.getTimeRange(dataSetURI, dataType)
for t in timeRange:
    print t
timeBegin = '1900-01-01T00:00:00.000Z'
timeEnd = '2011-11-01T00:00:00.000Z'
print


textFile = pyGDP.submitFeatureWeightedGridStatistics(OKshapefile, dataSetURI, dataType, timeBegin, timeEnd,usr_attribute, usr_value)

jd,precip=np.loadtxt(textFile,unpack=True,skiprows=3,delimiter=',', 
                     converters={0: mdates.strpdate2num('%Y-%m-%dT%H:%M:%SZ')})

print 'Some data:'
print precip[0:100]