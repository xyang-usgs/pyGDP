import pyGDP
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

"""
Instead of specifically specifying a value, we get request to get
the gmlID of these values and append them to a gmlID to be used
as an input instead of value.
"""
wisGMLID = pyGDP.getGMLIDs(shapefile, usr_attribute, 'Wisconsin')
michGMLID = pyGDP.getGMLIDs(shapefile, usr_attribute, 'Michigan')
minnGDMLID = pyGDP.getGMLIDs(shapefile, usr_attribute, 'Minnesota')
gmlIDs = wisGMLID + michGMLID + minnGDMLID

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
value = None
out1, out2, out3, out4 = pyGDP.featureWeightedGridStat(shapefile, dataSetURI, dataType, usr_attribute, value, timeRange[0], timeRange[0], gmlIDs)