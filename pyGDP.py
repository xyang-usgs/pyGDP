# dependencies: lxml.etree, ows.lib
# =============================================================================
# Copyright (c) 2012 USGS
#
# Author : Xao Yang <xyang@usgs.gov>
#
# Contact email: xyang@usgs.gov
# =============================================================================
from owslib.wps import WebProcessingService, WFSFeatureCollection, WFSQuery, GMLMultiPolygonFeatureCollection, monitorExecution
from owslib.ows import DEFAULT_OWS_NAMESPACE, XSI_NAMESPACE, XLINK_NAMESPACE
from owslib.wfs import WebFeatureService
from owslib.csw import namespaces as cswNamespace
from owslib.csw import schema as cswSchema
from owslib.csw import schema_location as cswSchema_location
from StringIO import StringIO
from urllib import urlencode
from urllib2 import urlopen
import urllib2 
import owslib.util as util
from owslib.etree import etree
import base64
import cgi
import sys

gdp_url = 'http://cida.usgs.gov//climate/gdp/proxy/http://cida-eros-gdp2.cr.usgs.gov:8082/geoserver/wfs' 
gdp_url = 'http://cida.usgs.gov/climate/gdp/proxy/http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs'

# namespace definition
WPS_DEFAULT_NAMESPACE="http://www.opengis.net/wps/1.0.0"
WPS_DEFAULT_SCHEMA_LOCATION = 'http://schemas.opengis.net/wps/1.0.0/wpsExecute_request.xsd'
WPS_DEFAULT_VERSION = '1.0.0'
WFS_NAMESPACE = 'http://www.opengis.net/wfs'
OGC_NAMESPACE = 'http://www.opengis.net/ogc'
GML_NAMESPACE = 'http://www.opengis.net/gml'
GML_SCHEMA_LOCATION = "http://schemas.opengis.net/gml/3.1.1/base/feature.xsd"
DRAW_NAMESPACE = 'gov.usgs.cida.gdp.draw'
DRAW_SCHEMA_LOCATION = 'http://cida.usgs.gov/qa/climate/derivative/xsd/draw.xsd'
SMPL_NAMESPACE = 'gov.usgs.cida.gdp.sample'
UPLD_NAMESPACE = 'gov.usgs.cida.gdp.upload'

# list of namespaces used by this module
namespaces = {
     None  : WPS_DEFAULT_NAMESPACE,
    'wps'  : WPS_DEFAULT_NAMESPACE,
    'ows'  : DEFAULT_OWS_NAMESPACE,
    'xlink': XLINK_NAMESPACE,
    'xsi'  : XSI_NAMESPACE,
    'wfs'  : WFS_NAMESPACE,
    'ogc'  : OGC_NAMESPACE,
    'gml'  : GML_NAMESPACE,
    'sample': SMPL_NAMESPACE,
    'upload': UPLD_NAMESPACE
}

def getDataType(dataSetURI, verbose=False):
    """
    Set up a get Data type request given a dataSetURI. Returns a list of all available data types.
    If verbose = True, will print on screen the waiting seq. for response document.
    """
    
    algorithm = 'gov.usgs.cida.gdp.wps.algorithm.discovery.ListOpendapGrids'
    return generateXMLRequest(dataSetURI, algorithm, method='getDataType', dataType=None, verbose=verbose)

def getTimeRange(dataSetURI, dataType, verbose=False):
    """
    Set up a get dataset time range request given a datatype and dataset uri. Returns the range
    of the earliest and latest time.
    If verbose = True, will print on screen the waiting seq. for response document.
    """
    
    algorithm = 'gov.usgs.cida.gdp.wps.algorithm.discovery.GetGridTimeRange'
    return generateXMLRequest(dataSetURI, algorithm, method='getDataSetTime', dataType=dataType, verbose=verbose)

# Given a dataSetURI, makes a wps call to cida..., retrives the response XML and gets back
# a list of data types
def generateXMLRequest(dataSetURI, algorithm, method, dataType=None, verbose=False):
    """
    Takes a dataset uri, algorithm, method, and datatype. This function will generate a simple XML document
    to make the request specified. (Only works for ListOpendapGrids and GetGridTimeRange). 
    
    Will return a list containing the info requested for (either data types or time range).
    """
    
    wps_Service = 'http://cida.usgs.gov/gdp/utility/WebProcessingService'
    POST = WebProcessingService(wps_Service, verbose=False)
        
    #<wps:Execute xmlns:wps="http://www.opengis.net/wps/1.0.0" 
    #             xmlns:ows="http://www.opengis.net/ows/1.1" 
    #             xmlns:xlink="http://www.w3.org/1999/xlink" 
    #             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    #             service="WPS" 
    #             version="1.0.0" 
    #             xsi:schemaLocation="http://www.opengis.net/wps/1.0.0 http://schemas.opengis.net/wps/1.0.0/wpsExecute_request.xsd">       
    root = etree.Element(util.nspath_eval('wps:Execute', namespaces), nsmap=namespaces)
    root.set('service', 'WPS')
    root.set('version', WPS_DEFAULT_VERSION)
    root.set(util.nspath_eval('xsi:schemaLocation', namespaces), '%s %s' % (namespaces['wps'], WPS_DEFAULT_SCHEMA_LOCATION) )
    
    # <ows:Identifier>gov.usgs.cida.gdp.wps.algorithm.discovery.ListOpendapGrids</ows:Identifier>
    identifierElement = etree.SubElement(root, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = algorithm
    
    # <wps:DataInputs>
    #    <wps:Input>
    #        <ows:Identifier>catalog-url</ows:Identifier>
    #        <wps:Data>
    #            <wps:LiteralData>'dataSetURI</wps:LiteralData>
    #        </wps:Data>
    #    <wps:Input>
    #        <wps:Identifier>allow-cached-response</wps:Identifier>
    #            <wps:Data>
    #                <wps:LiteralData>false</wps:LiteralData>
    #            </wps:Data>
    # </wps:DataInputs>
    dataInputsElement = etree.SubElement(root, util.nspath_eval('wps:DataInputs', namespaces))
    inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
    identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'catalog-url'
    dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
    literalElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
    literalElement.text = dataSetURI
    
    if method == 'getDataSetTime':
        inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
        identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
        identifierElement.text = 'grid'
        dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
        literalElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
        literalElement.text = dataType
    
    inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
    identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'allow-cached-response'
    dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
    literalElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
    literalElement.text = 'false'
    
    # <wps:ResponseForm storeExecuteResponse=true status=true>
    #    <wps:ResponseDocument>
    #        <ows:Output asReference=true>
    #            <ows:Identifier>result</ows:Identifier>
    #        </ows:Output>
    #    </wps:ResponseDocument>
    # </wps:ResponseForm>
    responseFormElement = etree.SubElement(root, util.nspath_eval('wps:ResponseForm', namespaces), attrib={'storeExecuteResponse': 'true', 'status' : 'true'})
    responseDocElement = etree.SubElement(responseFormElement, util.nspath_eval('wps:ResponseDocument', namespaces))
    outputElement = etree.SubElement(responseDocElement, util.nspath_eval('wps:Output', namespaces), attrib={'asReference': 'true'})
    identifierElement = etree.SubElement(outputElement, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'result'
    
    # change standard output to not display waiting status
    if not verbose:
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result   
    request = etree.tostring(root)
    
    execution = POST.execute(None, [], request=request)
    if method == 'getDataSetTime':
        seekterm = 'time'
    else:
        seekterm = 'name'
    if not verbose:
        sys.stdout = old_stdout
    return parseXMLNodesForTagText(execution.response, seekterm)


def parseXMLNodesForTagText(xml, tag):
    """
    Parses through a XML tree for text associated with specified tag.
    Returns a list of the text.
    """
    
    tag_text = []
    for node in xml.iter():
        if node.tag == tag:
            tag_text.append(node.text)
    return tag_text

def encodeZipFolder(zipfilePath):
    """
    Given a zip folder, this function will zip the folder and return its filepPath
    """
    
    #check extension
    if not zipfilePath.endswith('.zip'):
        print 'Wrong filetype.'
        return
    
    #encode the file
    with open(zipfilePath, 'rb') as fin:
        bytesRead = fin.read()
        encode= base64.b64encode(bytesRead)
    
    fout = open(zipfilePath, "w")
    fout.write(encode)
    fout.close()
    return zipfilePath

def uploadService(fileHandle):
    """
    Given a base64 encoded zip file, this function will generate a simple XML
    containing the file to submit to the geoserver.
    """
    
    
    fileO = open(fileHandle, "r")
    fileData = fileO.read()
    fileO.close()
    
    filename = fileHandle.split("/")
    filename = filename[len(filename)-1] # will get the filename
    filename = filename.replace(".zip", "")
    
    #Check to see if file is not online already
    fileCheckName = "upload:"+filename
    shapefiles = getShapefiles()
    if fileCheckName in shapefiles:
        print 'File exists already.'
        exit()
    
    wfsurl = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver'
    
    # Generates the XML document
    POST = WebProcessingService('http://cida.usgs.gov/climate/gdp/utility/WebProcessingService', verbose=False)
    
    #<wps:Execute xmlns:wps="http://www.opengis.net/wps/1.0.0" 
    #             xmlns:ows="http://www.opengis.net/ows/1.1" 
    #             xmlns:xlink="http://www.w3.org/1999/xlink" 
    #             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    #             service="WPS" 
    #             version="1.0.0" 
    #             xsi:schemaLocation="http://www.opengis.net/wps/1.0.0 http://schemas.opengis.net/wps/1.0.0/wpsExecute_request.xsd">       
    root = etree.Element(util.nspath_eval('wps:Execute', namespaces), nsmap=namespaces)
    root.set('service', 'WPS')
    root.set('version', WPS_DEFAULT_VERSION)
    root.set(util.nspath_eval('xsi:schemaLocation', namespaces), '%s %s' % (namespaces['wps'], WPS_DEFAULT_SCHEMA_LOCATION) )
    
    # <ows:Identifier>gov.usgs.cida.gdp.wps.algorithm.discovery.ListOpendapGrids</ows:Identifier>
    identifierElement = etree.SubElement(root, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'gov.usgs.cida.gdp.wps.algorithm.filemanagement.ReceiveFiles'
    
    # <wps:DataInputs>
    #    <wps:Input>
    #        <ows:Identifier>filename</ows:Identifier>
    #        <wps:Data>
    #            <wps:LiteralData>FILENAME</wps:LiteralData>
    #        </wps:Data>
    #    <wps:Input>
    #        <wps:Identifier>wfs-url</wps:Identifier>
    #            <wps:Data>
    #                <wps:LiteralData>false</wps:LiteralData>
    #            </wps:Data>
    # </wps:DataInputs>
    dataInputsElement = etree.SubElement(root, util.nspath_eval('wps:DataInputs', namespaces))
    
    inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
    identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'filename'
    dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
    literalElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
    literalElement.text = filename
    
    inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
    identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'wfs-url'
    dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
    literalElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
    literalElement.text = wfsurl

    # adding complex information
    inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
    identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'file'
    dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
    complexDataElement = etree.SubElement(dataElement, util.nspath_eval('wps:ComplexData', namespaces),
                                              attrib={"mimeType":"application/x-zipped-shp", "encoding":"Base64"} )
    complexDataElement.text = fileData
    
    # <wps:ResponseForm>
    #    <wps:ResponseDocument>
    #        <ows:Output>
    #            <ows:Identifier>result</ows:Identifier>
    #        </ows:Output>
    #    </wps:ResponseDocument>
    # </wps:ResponseForm>
    responseFormElement = etree.SubElement(root, util.nspath_eval('wps:ResponseForm', namespaces))
    responseDocElement = etree.SubElement(responseFormElement, util.nspath_eval('wps:ResponseDocument', namespaces))
    outputElement = etree.SubElement(responseDocElement, util.nspath_eval('wps:Output', namespaces))
    identifierElement = etree.SubElement(outputElement, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'result'
    outputElement = etree.SubElement(responseDocElement, util.nspath_eval('wps:Output', namespaces))
    identifierElement = etree.SubElement(outputElement, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'wfs-url'
    outputElement = etree.SubElement(responseDocElement, util.nspath_eval('wps:Output', namespaces))
    identifierElement = etree.SubElement(outputElement, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'featuretype'
    
    # now we have a complete XML upload request
    uploadRequest = etree.tostring(root)
    execution = POST.execute(None, [], request=uploadRequest)
    monitorExecution(execution)
    return filename

def getInput(listInput):
    """
    Given a list, this function will print out the list as well as
    prompt the user to select an item from the list.
    """
    
    for i in listInput:
        print i
    
    print '\n' + 'Choose from the list above:'
    usrinput = str(raw_input())
    while usrinput not in listInput:
        print 'not a valid input'
        usrinput = str(raw_input())
    return usrinput

def generateDescribeFeature(typename):
    """
    Sets up a cgi request to the wfs for features specified.
    """
    
    service_url = gdp_url
    
    qs = []
    if service_url.find('?') != -1:
            qs = cgi.parse_qsl(service_url.split('?')[1])

    params = [x[0] for x in qs]

    if 'service' not in params:
        qs.append(('service', 'WFS'))
    if 'request' not in params:
        qs.append(('request', 'DescribeFeatureType'))
    if 'version' not in params:
        qs.append(('version', '1.1.0'))
    if 'typename' not in params:
        qs.append(('typename', typename))

    urlqs = urlencode(tuple(qs))
    return service_url.split('?')[0] + '?' + urlqs

def getAttributes(shapefile):
    """
    Given a valid shapefile, this function will create a cgi call 
    returning a list of attributes associated with the shapefile.
    """
    
    urlen = generateDescribeFeature(shapefile)
    linesToParse = urlopen(urlen)
    
    # lines contains the lines with attributes embedded in them
    lines = getLinesContaining(linesToParse, 'xsd:element maxOccurs=')
    attributes = []
    
    # search the line
    for item in lines:
        word = getStringBetween('name=', item, ' ')
        # for attributes, will return "attribute", qoutes included, strip qoutes
        if word[1:len(word) - 1] != "the_geom":
            attributes.append(word[1: len(word) - 1])
    return attributes

def getStringBetween(beginterm, line, stopterm):
    """
    Helper function. Gets the string between beginterm and stopterm. 
    Line is the line or superstring to be examined.
    returns the string inbetween.
    """
    
    begin_index = line.find(beginterm)
    end_index = line.find(stopterm, begin_index)
    
    return line[begin_index + len(beginterm) : end_index ]

def getAllStringBetweenInLine(beginterm, line, stopterm):
    """
    Helper function. Gets the string between beginterm and stopterm.
    But works for repeating instances. 
    Line is the line or superstring to be examined.
    
    returns a list of all strings in between.
    """
    words = []
    
    begin_index = 0
    end_index = len(line)
    tmpline = line
    # start at the beginning
    while begin_index < len(line):
        begin_index = tmpline.find(beginterm)
        if begin_index != -1:
            end_index = tmpline.find(stopterm, begin_index)
            term = tmpline[begin_index + len(beginterm) : end_index ]
            tmpline = tmpline[end_index :]
            if term not in words:
                words.append(term)
            begin_index = end_index
            #print begin_index
        else:
            break
    return words

def getGMLIDString(GMLbeginterm, line, GMLstopterm, valBeginTerm, valStopTerm):
    """
    This function is specific to the output documents from the GDP. This
    function parses the XML document, to find the correct GMLID associated
    with a feature. Returns the list of values, and a dictionary [feature:id].
    """
    
    # we are searching for attr-value, gml:id pair
    value = []
    ntuple = []
    begin_index = 0
    end_index = len(line)
    tmpline = line
    # start at the beginning
    while begin_index < len(line):
        begin_index = tmpline.find(GMLbeginterm)
        if begin_index != -1:
            end_index = tmpline.find(GMLstopterm, begin_index)
            # we get the gml term
            gmlterm = tmpline[begin_index + len(GMLbeginterm) : end_index ]
            
            # now we get the attribute value
            begin_index2 = tmpline.find(valBeginTerm)
            end_index2   = tmpline.find(valStopTerm, begin_index2)    
            
            valTerm = tmpline[begin_index2 + len(valBeginTerm) : end_index2 ]
            #tuple: attr-value, gml:id
            tmpTuple = valTerm, gmlterm
            ntuple.append(tmpTuple)
            
            tmpline = tmpline[end_index2 :]
            
            if valTerm not in value:
                value.append(valTerm)
            begin_index = end_index
            #print begin_index
        else:
            break
    return value, ntuple

def generateValueFeature(typename, attribute):
    """
    Simliar to generateAttribute, this function, given a attribute
    and a typename or filename will return a list of values associated
    with the file and the attribute chosen.
    """
    service_url = gdp_url
    
    qs = []
    if service_url.find('?') != -1:
            qs = cgi.parse_qsl(service_url.split('?')[1])

    params = [x[0] for x in qs]

    if 'service' not in params:
        qs.append(('service', 'WFS'))
    if 'request' not in params:
        qs.append(('request', 'GetFeature'))
    if 'version' not in params:
        qs.append(('version', '1.1.0'))
    if 'typename' not in params:
        qs.append(('typename', typename))
    if 'propertyname' not in params:
        qs.append(('propertyname', attribute))

    urlqs = urlencode(tuple(qs))
    return service_url.split('?')[0] + '?' + urlqs

def getGMLIDs(shapefile, attribute, value):
    tuples = getTuples(shapefile, attribute)
    return getFilterID(tuples, value)

def getValues(shapefile, attribute, getTuples='false'):
    """
    Similar to get attributes, given a shapefile and a valid attribute this function
    will make a call to the Web Feature Services returning a list of values associated
    with the shapefile and attribute.
    
    If getTuples = True, will also return the tuples of [feature:id]  along with values [feature]
    """
    
    urlen = generateValueFeature(shapefile, attribute)
    inputObject = urlopen(urlen)
    shapefileterm = shapefile.split(':')
    
    strinx = inputObject.read()
    lines = strinx.split('\n')
    
    # gets the tag/namespace name
    stringSnippet = getStringBetween('<', lines[1], ':'+attribute+'>')
    stringSnippet = stringSnippet.split('<')
    shapefileterm[0] = stringSnippet[len(stringSnippet) - 1]
    
    # look for this pattern: <term[0]:attribute>SOUGHTWORD</term[0]:attribute>
    values, tuples = getGMLIDString('gml:id="', lines[1], '">', '<'+shapefileterm[0] + 
                                    ':' + attribute + '>', '</' +shapefileterm[0] +':' + 
                                    attribute + '>')
    if getTuples=='true':
        return sorted(values), sorted(tuples)
    elif getTuples=='only':
        return sorted(tuples)
    else:
        return sorted(values)

def getTuples(shapefile, attribute):
    """
    Will return the dictionary tuples only.
    """
    return getValues(shapefile, attribute, getTuples='only')
    
def getFilterID(tuples, value):
    """
    Given a the tuples generated by getTuples and a value, will return a list of gmlIDs
    associated with the value specified.
    """
    value = str(value)
    filterID = []
    for item in tuples:
        if item[0] == value:
            filterID.append(item[1])
    return filterID

def getLinesContaining(linesToParse, term):
    """
    Given a document, goes through the document and for each line with the
    occurence of the specified term, add that line to a list.
    Returns the list.
    """
    line_list = []
    for line in linesToParse:
        if term in line:
            line_list.append(line)
    linesToParse.close()
    return line_list

def __filterSubOne(filterID):
    """
    Currently, gmlIDs returned are 1 greater than the actual ids.
    This function adjusts the gmlID to their actual values.
    """
    
    gmlIDs = filterID.split('.')
    no = int(gmlIDs[1])
    if (no - 1) < 1:
        return None
    filterID = gmlIDs[0] + '.' + str(no - 1)
    return filterID

def featureWeightedGridStat(shpfile, dataSetURI, dataType, attribute, value, startTime, endTime, gmlIDs=None,
                                coverage='true', delim='COMMA', stat='MEAN', grpby='STATISTIC', timeStep='false', summAttr='false'):
    """
    Inputs: Shapefile, datasetURI, a dataType, an attribute, a value, a start Time, and an endTime
    optional inputs: coverage, delimiters, stat, group by, time step, and summarize feature attribute
    output: dataType header, value descriptions, header description, result values
    
    Makes a WPS call to the GDP. Returns with the valid information. 
    """
    
    tmpID = []
    if gmlIDs is None:
        if type(value) == type(tmpID):
            for v in value:
                tuples = getTuples(shpfile, attribute)
                tmpID = getFilterID(tuples, v)
                gmlIDs = gmlIDs + tmpID
        else:
            tuples = getTuples(shpfile, attribute)
            gmlIDs = getFilterID(tuples, value)
    
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService')
    wfsUrl = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs'
    query = WFSQuery(shpfile, propertyNames=["the_geom", attribute], filters=gmlIDs)
    featureCollection = WFSFeatureCollection(wfsUrl, query)
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
    inputs = [ ("FEATURE_ATTRIBUTE_NAME",attribute),
           ("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataType),         
           ("TIME_START",startTime),
           ("TIME_END",endTime),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("DELIMITER",delim),
           ("STATISTICS",stat),
           ("GROUP_BY", grpby),
           ("SUMMARIZE_TIMESTEP", timeStep),
           ("SUMMARIZE_FEATURE_ATTRIBUTE",summAttr),
           ("FEATURE_COLLECTION", featureCollection)
          ]
    
    print 'Executing Request...'
    # redirects the standard output to avoid printing request status
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    
    # executes the request
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    monitorExecution(execution, download=True)    
    
    # sets the standard output back to original
    sys.stdout = old_stdout
    result_string = result.getvalue()
    
    #parses the redirected output to get the filepath of the
    #saved file
    output = result_string.split('\n')
    print output[len(output) - 3]
    print output[len(output) - 2]
    tmp = output[len(output) - 2].split(' ')
    fname = tmp[len(tmp)-1]
    
    return getOutputDataFromFile(fname, delim)

def sumbitRequestPolygon(polygon, dataSetURI, dataType, attribute, value, startTime, endTime,
                                coverage='true', delim='COMMA', stat='MEAN', grpby='STATISTIC', timeStep='false', summAttr='false'):

    """
    Submit a wps request with a polygon (rather than shapefile). Format of the polygon is as followed:
    eg: polygon = [(points, points), (points, points), (points, points), (points, points) ... (points, points)]
    """
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService', verbose=verbose, skip_caps=True)
    featureCollection = GMLMultiPolygonFeatureCollection( [polygon] )
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
     
    inputs = [ ("FEATURE_ATTRIBUTE_NAME",attribute),
           ("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataType),         
           ("TIME_START",startTime),
           ("TIME_END",endTime),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("DELIMITER",delim),
           ("STATISTICS",stat),
           ("GROUP_BY", grpby),
           ("SUMMARIZE_TIMESTEP", timeStep),
           ("SUMMARIZE_FEATURE_ATTRIBUTE",summAttr),
           ("FEATURE_COLLECTION", featureCollection)
          ]
    output = "OUTPUT"
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    monitorExecution(execution)    

def __makeExampleRequest(verbose=False):
    """
    Exampe request. Source: OWSLIB wps
    """
    
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService', verbose=verbose, skip_caps=True)
    polygon = [(-102.8184, 39.5273), (-102.8184, 37.418), (-101.2363, 37.418), (-101.2363, 39.5273), (-102.8184, 39.5273)]
    featureCollection = GMLMultiPolygonFeatureCollection( [polygon] )
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
    inputs = [ ("FEATURE_ATTRIBUTE_NAME","the_geom"),
           ("DATASET_URI", "dods://cida.usgs.gov/qa/thredds/dodsC/derivatives/derivative-days_above_threshold.pr.ncml"),
           ("DATASET_ID", "ensemble_b1_pr-days_above_threshold"),
           ("TIME_START","2010-01-01T00:00:00.000Z"),
           ("TIME_END","2011-01-01T00:00:00.000Z"),
           ("REQUIRE_FULL_COVERAGE","false"),
           ("DELIMITER","COMMA"),
           ("STATISTICS","MEAN"),
           ("GROUP_BY","STATISTIC"),
           ("SUMMARIZE_TIMESTEP","false"),
           ("SUMMARIZE_FEATURE_ATTRIBUTE","false"),
           ("FEATURE_COLLECTION", featureCollection)
          ]
    output = "OUTPUT"
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    # alternatively, submit a pre-made request specified in an XML file
    #request = open('../tests/wps_USGSExecuteRequest1.xml','r').read()
    #execution = wps.execute(None, [], request=request)

    # The monitorExecution() function can be conveniently used to wait for the process termination
    # It will eventually write the process output to the specified file, or to the file specified by the server.
    monitorExecution(execution)    

def featureCoverageOPenDAP(shpfile, dataSetURI, dataType, attribute, value, startTime, endTime, coverage='true', verbose=False, gmlIDs=None):
    """
    Makes a featureCoverageOPenDap request. Takes a shapefile, datasetURI, datatype, attribute,
    value, start and end time. Should specify coverage='true' or 'false' 
    """
    
    tmpID = []
    if gmlIDs is None:
        if type(value) == type(tmpID):
            for v in value:
                tuples = getTuples(shpfile, attribute)
                tmpID = getFilterID(tuples, v)
                gmlIDs = gmlIDs + tmpID
        else:
            tuples = getTuples(shpfile, attribute)
            gmlIDs = getFilterID(tuples, value)

    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService')
    wfsUrl = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs'
    query = WFSQuery(shpfile, propertyNames=["the_geom", attribute], filters=gmlIDs)
    featureCollection = WFSFeatureCollection(wfsUrl, query)
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageOPeNDAPIntersectionAlgorithm'
    inputs = [ ("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataType),         
           ("TIME_START",startTime),
           ("TIME_END",endTime),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("FEATURE_COLLECTION", featureCollection)
          ]

    # executes the request
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    monitorExecution(execution, download=True) 

def featureCoverageWCSIntersection(shpfile, dataSetURI, dataType, attribute, value, coverage='true', verbose=False, gmlIDs=None):
    """
    Makes a featureCoverageWCSInteraction request. Takes a shapefile, datasetURI, datatype, attribute,
    and value. Should specify coverage='true' or 'false' 
    """
    
    tmpID = []
    if gmlIDs is None:
        if type(value) == type(tmpID):
            for v in value:
                tuples = getTuples(shpfile, attribute)
                tmpID = getFilterID(tuples, v)
                gmlIDs = gmlIDs + tmpID
        else:
            tuples = getTuples(shpfile, attribute)
            gmlIDs = getFilterID(tuples, value)
    
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService')
    wfsUrl = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs'
    query = WFSQuery(shpfile, propertyNames=["the_geom", attribute], filters=gmlIDs)
    featureCollection = WFSFeatureCollection(wfsUrl, query)
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageIntersectionAlgorithm'
    inputs = [("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataType),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("FEATURE_COLLECTION", featureCollection)
          ]
    
    # executes the request
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    monitorExecution(execution, download=True)

def featureCategoricalGridCoverage(shpfile, dataSetURI, dataType, attribute, value, coverage='True', delim='COMMA', verbose=False, gmlIDs=None):
    """
    Makes a featureCoverageOPenDap request. Takes a shapefile, datasetURI, datatype, attribute,
    and value. Should specify coverage='true' or 'false' and delimiter = 'COMMA' or 'TAB' or 'SPACE'
    """
    
    tmpID = []
    if gmlIDs is None:
        if type(value) == type(tmpID):
            for v in value:
                tuples = getTuples(shpfile, attribute)
                tmpID = getFilterID(tuples, v)
                gmlIDs = gmlIDs + tmpID
        else:
            tuples = getTuples(shpfile, attribute)
            gmlIDs = getFilterID(tuples, value)
    
    wps = WebProcessingService('http://cida.usgs.gov/gdp/process/WebProcessingService', verbose=verbose)    
    wfsUrl = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs'
    query = WFSQuery(shpfile, propertyNames=["the_geom", attribute], filters=gmlIDs)
    featureCollection = WFSFeatureCollection(wfsUrl, query)
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCategoricalGridCoverageAlgorithm'
    inputs = [ ("FEATURE_ATTRIBUTE_NAME",attribute),
           ("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataType),         
           ("DELIMITER", delim),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("FEATURE_COLLECTION", featureCollection)
          ]
    
    # executes the request
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    monitorExecution(execution, download=True)

def getOutputDataFromFile(fname, delim):
    """
    Given a filepath for an output file from the GDP and the specified document delimiter,
    this function will parse the document and return a datatype header, value header, 
    description header, and data row. 
    """
    try:
        f = open(fname)
        rows = f.readlines()
        f.close()
    except IOError:
        print 'Issue with WPS call resulted in no data. Check dataSet.'
    
    try:
        delimitor = None
        if delim == 'TAB':
            delimitor = '\t'
        elif delim == 'COMMA':
            delimitor = ','
        
        dataType = rows[0][:-1]
        values   = rows[1][:-1].split(delimitor)
        description = rows[2][:-1].split(delimitor)
        values[0] = 'TIME'
        i = 3
        dataEntries = []
        while i < len(rows):
            dataEntries.append(rows[i][:-1].split(delimitor)) 
            i = i + 1
        return dataType,values,description, dataEntries
    except Exception:
        print 'Output error. Refer to previous error message.'

def submitFeatureWeightedXMLRequest(xml):
    """
    Given a well formed XML, submit the xml onto WPS
    """
    try:
        request = open(xml).read()
    except:
        print("I/O error.")
    
    verbose = False
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService', verbose=verbose)
    execution = wps.execute(None, [], request=request)
    monitorExecution(execution, download=True)

def getShapefiles():
    """
    Returns a list of available files currently on geoserver.
    """
    wfs = WebFeatureService(gdp_url)
    shapefiles = wfs.contents.keys()
    return shapefiles

# Gets a list of valid dataset URIs, currently hardcoded. WILL need to make CWS call
def getDataSetURI():
    
    """
    This function will not be implemented. This function is only implemented to give a few dataset URIs which may not work
    with certain datasets and will with others within the bounding box requirements.
    """ 
    print 'The dataSetURI outputs a select few URIs and may not work with the specific shapefile you are providing.'
    print 'To ensure compatibility, we recommend selecting a dataSetURI that is specific to the shapefile.' 
    print 'Or you may utilize the web gdp @ http://cida.usgs.gov/climate/gdp/ to get a dataSet matching your specified shapefile.'
    print
    
    dataSetURIs = ['http://regclim.coas.oregonstate.edu:8080/thredds/dodsC/regcmdata/NCEP/merged/monthly/RegCM3_A2_monthly_merged_NCEP.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/conus_grid.w_meta.ncml',
                   'http://cida.usgs.gov/qa/thredds/dodsC/prism',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/maurer/maurer_brekke_w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/alaska_grid.w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/gmo/GMO_w_meta.ncml']
    return dataSetURIs

