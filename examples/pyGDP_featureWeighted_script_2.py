import pyGDP

pyGDP = pyGDP.pyGDPwebProcessing()
shapefiles = pyGDP.getShapefiles()
print 'Available shapefiles: '
for shapefile in shapefiles:
    print shapefile
print 

# Grab the file and get its attributes:
shapefile = 'sample:CSC_Boundaries'
attributes = pyGDP.getAttributes(shapefile)
for attr in attributes:
    print attr
print

# Grab the values from 'OBJECTID' and 'upload:OKCNTYD'
usr_attribute = 'area_name'
values = pyGDP.getValues(shapefile, usr_attribute)
for v in values:
    print v
print

usr_value = 'Southwest'
dataSetURI = 'dods://cida-eros-thredds1.er.usgs.gov:8082/thredds/dodsC/dcp/conus_grid.w_meta.ncml'
dataTypes = pyGDP.getDataType(dataSetURI)
for d in dataTypes:
    print d
dataType = 'bcm2_a1b_tmax'

timeBegin = '1960-01-01T00:00:00.000Z'
timeEnd = '1970-01-21T00:00:00.000Z'
outputPath = pyGDP.submitFeatureWeightedGridStatistics(shapefile, dataSetURI, dataType, timeBegin, timeEnd, usr_attribute, usr_value, gmlIDs=None, verbose=True)

