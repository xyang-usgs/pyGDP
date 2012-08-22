import pyGDP

def getInput(listInput):
    
    for i in listInput:
        print i
    
    print '\n' + 'Choose from the list above:'
    usrinput = str(raw_input())
    while usrinput not in listInput:
        print 'not a valid input'
        usrinput = str(raw_input())
    return usrinput

def main():
    gdp = pyGDP.pyGDPwebProcessing()
    sfiles = gdp.getShapefiles()
    for s in sfiles:
        print s
    
    shapefile = 'sample:CONUS_States'
    
    print
    print 'Get Attributes:'
    attributes = gdp.getAttributes(shapefile)
    for a in attributes:
        print a
    
    print
    print 'Get values:'
    values = gdp.getValues(shapefile, 'STATE')
    for v in values:
        print v
        
    print
    print 'Getting available Dataset URIS'
    datasetURIs = gdp.getDataSetURI()
    dataSetURI = getInput(datasetURIs)
    
    print ''
    print 'Getting available dataTypes'
    dataTypes = gdp.getDataType(dataSetURI)
    dataType = getInput(dataTypes)
    
    print 
    print 'Getting time range from dataset'
    
    timeRange = gdp.getTimeRange(dataSetURI, dataType)
    for i in timeRange:
        print i
    
    print
    print 'Submitting request'
    output = gdp.submitFeatureWeightedGridStatistics(shapefile, dataSetURI, dataType, timeRange[0], timeRange[0], 'STATE', 'Wisconsin')
    print output
    
if __name__=="__main__":
    main()