# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from IPython.core.display import HTML
from IPython.core.display import Image
Image('http://www-tc.pbs.org/kenburns/dustbowl/media/photos/s2571-lg.jpg')

# <codecell>

#Above: Dust storm hits Hooker, OK, June 4, 1937. So how much precip really was there during the dust bowl years?

# <codecell>

import pyGDP
# if we have our shapefile as a zip, base 64 encode it and upload it to geoserver
filePath = 'OKCNTYD.zip'
fileHandle = pyGDP.encodeZipFolder(filePath)
#OKshapeFile = pyGDP.uploadService(fileHandle)

# <codecell>

# Above: We have sucessfully uploaded our shapefile onto geoserver.

# <codecell>

# Now, if we used GDP on the browser, we would navigate through something liks this:
HTML('<iframe src=http://screencast.com/t/K7KTcaFrSUc width=800 height=600>')

# <codecell>

# With pyGDP, we can utilize python.
shapefiles = pyGDP.getShapefiles()
print 'Available Shapefiles:'
for s in shapefiles:
    print s

# <codecell>

# the shapefile we want is 'upload:OKCNTYD'
OKshapeFile = 'upload:OKCNTYD'
# In this particular example, we are interested in attribute = 'OBJECTID' and value = '13'
attributes = pyGDP.getAttributes(OKshapeFile)
for a in attributes:
    print a

# <codecell>

user_attribute = 'OBJECTID'
values = pyGDP.getValues(OKshapeFile, user_attribute)
for v in values:
    print v

# <codecell>

user_value = 13

#Once we have our shapefile, attribute, and value, we pick a dataset we are interested in.
dataSets = pyGDP.getDataSetURI()
for d in dataSets:
    print d

# <codecell>

dataSetURI = 'dods://cida.usgs.gov/qa/thredds/dodsC/prism'
#Get the available dataTypes
dataTypes = pyGDP.getDataType(dataSetURI)
for d in dataTypes:
    print d

# <codecell>

user_dataType = 'ppt'
#get the time range for the dataSet
timeRange = pyGDP.getTimeRange(dataSetURI, user_dataType)
for t in timeRange:
    print t

# <codecell>

timeBegin = '1900-01-01T00:00:00Z'
timeEnd = '2011-11-01T00:00:00Z'

# <codecell>

# Once we have our shapefile, attribute, value, dataset, datatype, and timerange as inputs, we can go ahead
# and submit our request.

out1, out2, out3, out4 = pyGDP.submitRequest(OKshapeFile, dataSetURI, user_dataType, user_attribute, user_value, timeBegin, timeEnd)

# <codecell>

print out1
print out2
print out3
print out4

# <codecell>

# Above, our data is displayed.

# <codecell>

import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

# load historical PRISM precip
jd,precip=np.loadtxt('5220291858966525635OUTPUT.e956d6e9-6b2c-4395-90f2-cb5330df2fb7',unpack=True,skiprows=3,delimiter=',', 
                     converters={0: mdates.strpdate2num('%Y-%m-%dT%H:%M:%SZ')})

# <codecell>

def boxfilt(data,boxwidth):
    from scipy import signal
    import numpy as np
    weights=signal.get_window('boxcar',boxwidth)
    dataf=np.convolve(data,weights/boxwidth,mode='same')
    dataf=np.ma.array(dataf)
    dataf[:boxwidth/2]=np.nan
    dataf[-boxwidth/2:]=np.nan
    dataf=np.ma.masked_where(dataf==np.nan,dataf)
    return dataf

# <codecell>

# PRISM data is monthly:  filter over 36 months
plp=boxfilt(precip,36)

fig=plt.figure(figsize=(10,2), dpi=80) 
ax1 = fig.add_subplot(111)
g1=ax1.plot_date(jd,plp,fmt='b-')
g2=ax1.plot_date(jd,0*jd+np.mean(precip),fmt='k-')
fig.autofmt_xdate()
plt.title('Average Precip for Texas County, Oklahoma, calculated via GDP using PRISM data ')

# <codecell>

HTML('<iframe src=http://www.ipcc.ch/publications_and_data/ar4/wg1/en/spmsspm-projections-of.html width=900 height=350>')

# <codecell>

# Below: The two files can be obtained via the same method as above. For scimplicity, we have already retrieved the data.
# Load the GDP result for: CCSM A1F1 ("business as usual") 
jd_a1f1,precip_a1f1 =np.loadtxt('gdp_texas_county_ccsm_a1f1.csv',unpack=True,skiprows=3,delimiter=',',
    converters={0: mdates.strpdate2num('%Y-%m-%dT%H:%M:%SZ')}) 
# Load the GDP result for:  CCSM B1 ("eco friendly")
jd_b1,precip_b1 =np.loadtxt('gdp_texas_county_ccsm_b1.csv',unpack=True,skiprows=3,delimiter=',',
    converters={0: mdates.strpdate2num('%Y-%m-%dT%H:%M:%SZ')}) 

# <codecell>

# Hayhoe climate downscaling is hourly: filter over 1080 days (36 months)
plp_a1f1=boxfilt(precip_a1f1,1080)
plp_b1=boxfilt(precip_b1,1080)
#plp_a1b_c=boxfilt(precip_a1b_c,36)
fig=plt.figure(figsize=(15,3), dpi=80) 
ax1 = fig.add_subplot(111)
fac=30. # convert from mm/day to mm/month (approx)
# plot A1F1 scenario
g1=ax1.plot_date(jd_a1f1,plp_a1f1*fac,fmt='b-')
# plot B1 scenario 
g2=ax1.plot_date(jd_b1,plp_b1*fac,fmt='g-')
# plot PRISM data
g3=ax1.plot_date(jd,plp,fmt='r-')  # for some reason when I add this the labels get borked
ax1.xaxis.set_major_locator(mdates.YearLocator(10,month=1,day=1))
ylabel('mm/month')
plt.title('Average Precip for Texas County, Oklahoma, calculated via GDP using Hayhoe Downscaled GCM ')

# <codecell>

jd_a1b_c,precip_a1b_c =np.loadtxt('gdp_texas_county_bias_corrected_ccsm_a1b.csv',unpack=True,skiprows=3,delimiter=',',
    converters={0: mdates.strpdate2num('%Y-%m-%dT%H:%M:%SZ')}) 
precip_a1b_c[100:105]

# <codecell>

import netCDF4

def mean_precip(nc,bbox=None,start=None,stop=None):
    lon=nc.variables['lon'][:]
    lat=nc.variables['lat'][:]
    tindex0=netCDF4.date2index(start,nc.variables['time'],select='nearest')
    tindex1=netCDF4.date2index(stop,nc.variables['time'],select='nearest')
    bi=(lon>=box[0])&(lon<=box[2])
    bj=(lat>=box[1])&(lat<=box[3])
    p=nc.variables['precip_mean'][tindex0:tindex1,bj,bi]
    latmin=np.min(lat[bj])
    p=np.mean(p,axis=0)
    lon=lon[bi]
    lat=lat[bj]
    return p,lon,lat

url='http://geoport.whoi.edu/thredds/dodsC/prism3/monthly'
box = [-102,36.5,-101,37]  # Bounding box for Texas County, Oklahoma
nc=netCDF4.Dataset(url)
p,lon,lat=mean_precip(nc,bbox=box,start=datetime.datetime(1936,11,1,0,0),stop=datetime.datetime(1937,4,1,0,0))
p2,lon,lat=mean_precip(nc,bbox=box,start=datetime.datetime(2009,11,1,0,0),stop=datetime.datetime(2010,4,1,0,0))
latmin=np.min(lat)

# <codecell>

import matplotlib.pylab as plt
fig=plt.figure(figsize=(10,5), dpi=80) 
ax = fig.add_axes([0.1, 0.15, 0.3, 0.8])
pc = ax.pcolormesh(lon, lat, p, cmap=plt.cm.jet_r)
ax.set_aspect(1.0/np.cos(latmin * np.pi / 180.0))
plt.title('Precip in Texas County, Oklahoma: Winter 1936-1937')

cbax = fig.add_axes([0.45, 0.3, 0.03, 0.4])
cb = plt.colorbar(pc, cax=cbax,  orientation='vertical')
cb.set_label('Precip (mm/month)')

ax2 = fig.add_axes([0.6, 0.15, 0.3, 0.8])
pc2 = ax2.pcolormesh(lon, lat, p2, cmap=plt.cm.jet_r)
ax2.set_aspect(1.0/np.cos(latmin * np.pi / 180.0))
plt.title('Precip in Texas County, Oklahoma: Winter 2010-2011')

cbax2 = fig.add_axes([0.95, 0.3, 0.03, 0.4])
cb2 = plt.colorbar(pc2, cax=cbax2,  orientation='vertical')
cb2.set_label('Precip (mm/month)')


plt.show()

# <codecell>

fig=plt.figure(figsize=(10,5), dpi=80) 
ax3 = fig.add_axes([0.1, 0.15, 0.3, 0.8])
pc3 = ax3.pcolormesh(lon, lat, p2-p, cmap=plt.cm.jet_r)
ax3.set_aspect(1.0/np.cos(latmin * np.pi / 180.0))
plt.title('Precip in Texas County, Oklahoma: Difference 2011-1937')

cbax3 = fig.add_axes([0.45, 0.3, 0.03, 0.4])
cb3 = plt.colorbar(pc3, cax=cbax3,  orientation='vertical')
cb3.set_label('Precip (mm/month)')

# <codecell>


