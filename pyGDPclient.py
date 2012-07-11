import pyGDP
from tkFileDialog import askopenfilename

def openFile():
    filePath = askopenfilename(filetypes=[("all","*"),("shp","*.shp")])
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
    print filePath
    #print attributes
    attributes = pyGDP.getAttributesFromShape(filePath)
    usr_attribute = getInput(attributes)
    
    values = pyGDP.getValuesFromShape(filePath, usr_attribute)
    usr_value = getInput(values)
    
    
    # we now have user_attribute & user_value
    # time to select a datasetURI, data type, and time
    dataSetURIs = pyGDP.getDataSetURI()
    
    # dataSet = getInput(dataSetURIs)
    dataSet = dataSetURIs[4]
    dataTypes = pyGDP.getDataType(dataSet)
    for i in dataTypes:
        print i
    
    timeRange = pyGDP.getDataSetTimeRange(dataSet, dataTypes[0]) 
    for i in timeRange:
        print i
    
    d1,d2,d3,d4 = pyGDP.submitFeatureWeightedRequest(filePath, dataSet, dataTypes[0], usr_attribute, usr_value, timeRange[0], timeRange[0])
    
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