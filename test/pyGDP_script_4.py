import glob
import pyGDP
import matplotlib.dates as mdates
import numpy as np

"""
This example shows how easy it is to make a call, if all
inputs are known before hand.
"""

fileList = []
for f in glob.glob("*"):
    fileList.append(f)


shapefile = 'sample:simplified_HUC8s'
user_attribute = 'REGION'
user_value = 'Great Lakes Region'
dataSet = 'dods://cida.usgs.gov/thredds/dodsC/gmo/GMO_w_meta.ncml'
dataType = 'Prcp'
timeBegin = '1970-01-23T00:00:00.000Z'
timeEnd = '1979-01-23T00:00:00.000Z'

pyGDP.submitRequest(shapefile, dataSet, dataType, user_attribute, user_value, timeBegin, timeEnd)

textFile = ''
for f in glob.glob("*"):
    if f not in fileList:
        textFile = f
        
jd,precip =np.loadtxt(textFile,unpack=True,skiprows=3,delimiter=',',
    converters={0: mdates.strpdate2num('%Y-%m-%dT%H:%M:%SZ')}) 

print precip[0:100]

#pyGDP.makeExampleRequest()