import pyGDP

pyGDP = pyGDP.pyGDPwebProcessing()

shapefile = 'sample:CONUS_States'
attribute = 'STATE'
value = 'Alabama'

dataSetURI = 'dods://cida.usgs.gov/thredds/dodsC/gmo/GMO_w_meta.ncml'

dataType = 'Prcp'
timeStart = '1950-01-01T00:00:00.000Z'
timeEnd = '1951-01-31T00:00:00.000Z'

pyGDP.submitFeatureCoverageOPenDAP(shapefile, dataSetURI, dataType, timeStart, timeEnd, attribute, value, verbose=True)
