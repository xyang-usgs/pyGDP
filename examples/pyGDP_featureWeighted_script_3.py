import pyGDP

pyGDP = pyGDP.pyGDPwebProcessing()
"""
This example script calls into the geoserver to obtain
the name of the shapefile 'sample:CONUS_States' sets up the
proper inputs and submits a request into GDP.
"""

shapefiles = pyGDP.getShapefiles()
print 'Available shapefiles: '
for shapefile in shapefiles:
    print shapefile
print 

# Grab the file and get its attributes:
shapefile = 'sample:CONUS_States'
attributes = pyGDP.getAttributes(shapefile)
for attr in attributes:
    print attr
print

# Grab the values from 'OBJECTID' and 'upload:OKCNTYD'
usr_attribute = 'STATE'
values = pyGDP.getValues(shapefile, usr_attribute)
for v in values:
    print v
print

# our shapefile = 'upload:OKCNTYD', usr_attribute = 'OBJECTID', and usr_value = 13
# We get the dataset URI that we are interested in
dataSetURIs = pyGDP.getDataSetURI()
for d in dataSetURIs:
    print d

# Set our datasetURI
dataSetURI = 'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/gmo/GMO_w_meta.ncml'
# Get the available data types associated with the dataset
dataType = 'Prcp'
# Get available time range on the dataset
timeRange = pyGDP.getTimeRange(dataSetURI, dataType)
for t in timeRange:
    print t

"""
Instead of submitting in a value, we submit a list of gmlIDs associated
with either a small portion of that value, or multiple values.
"""
values = ['Wisconsin', 'Michigan', 'Minnesota']
path = pyGDP.submitFeatureWeightedGridStatistics(shapefile, dataSetURI, dataType, timeRange[0], timeRange[0], usr_attribute, values)
print path