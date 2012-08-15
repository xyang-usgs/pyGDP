import pyGDP
from tkFileDialog import askopenfilename

def openFile():
    filePath = askopenfilename(filetypes=[("all","*"),("zip","*.zip")])
    try:
        open(filePath).read()
    except IOError:
        print("I/O error.")
        exit()
    return filePath

def openXML():
    filePath = askopenfilename(filetypes=[("all","*"),("xml","*.xml")])
    try:
        open(filePath).read()
    except IOError:
        print("I/O error.")
        exit()
    return filePath

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
    
    filePath = openFile()
    # encode the zip file
    fileHandle = pyGDP.encodeZipFolder(filePath)
    #upload the file to geoserver
    pyGDP.uploadService(fileHandle)
    # now the file should be online
    
    print 
    shapefiles = pyGDP.getShapefiles()
    for k in shapefiles:
        print k
    
    shpfile = getInput(shapefiles)
    
    print ''
    print 'Getting Attributes'
    attributes = pyGDP.getAttributes(shpfile)
    usr_attribute = getInput(attributes)
    
    print ''
    print 'Getting Values'
    values = pyGDP.getValues(shpfile, usr_attribute)
    usr_value = getInput(values)
    
    print ''
    print 'Getting available DataSet URIs'
    # we now have user_attribute & user_value
    # time to select a datasetURI, data type, and time
    dataSetURIs = pyGDP.getDataSetURI()
    # dataSet = getInput(dataSetURIs)
    dataSetURI = getInput(dataSetURIs)
    
    print ''
    print 'Getting available dataTypes'
    # get the available variables in the dataset
    dataTypes = pyGDP.getDataType(dataSetURI)
    dataType = getInput(dataTypes)
    
    print ''
    print 'getting Time from DataSet'
    
    # get the begin and the end time range
    timeRange = pyGDP.getTimeRange(dataSetURI, dataType)
    for i in timeRange:
        print i
    
    print ''
    print 'Submitting request'
    d1,d2,d3,d4 = pyGDP.featureWeightedGridStat(shpfile, dataSetURI, dataType, usr_attribute, usr_value, timeRange[0], timeRange[0])
    #pyGDP.submitFeatureWeightedRequest(shpfile, dataSetURI, dataTypes[0], usr_attribute, usr_value, timeRange[0], timeRange[0])
    
    print d1
    print d2
    print d3
    print d4
    
    
    """
    # instantiate WPS client
    filePath = openXML()
    # another request
    pyGDP.submitFeatureWeightedXMLRequest(filePath)
    """
    
if __name__ == "__main__":
    main()