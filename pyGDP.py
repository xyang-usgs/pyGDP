# dependencies: lxml.etree, ows.lib
# =============================================================================
# Copyright (c) 2012 USGS
#
# Author : Xao Yang <xyang@usgs.gov>
#
# Contact email: xyang@usgs.gov
# =============================================================================
from owslib.wps import WebProcessingService, WPSExecution, WFSFeatureCollection, WFSQuery, GMLMultiPolygonFeatureCollection, monitorExecution, printInputOutput
from owslib.ows import DEFAULT_OWS_NAMESPACE, XSI_NAMESPACE, XLINK_NAMESPACE, \
                       OWS_NAMESPACE_1_0_0, ServiceIdentification, ServiceProvider, OperationsMetadata
from owslib.wfs import WebFeatureService
from StringIO import StringIO
from urllib import urlencode
from urllib2 import urlopen
import owslib.util as util
import lxml.etree as etree
import base64, cgi, sys

gdp_url = 'http://cida.usgs.gov//climate/gdp/proxy/http://cida-eros-gdp2.cr.usgs.gov:8082/geoserver/wfs' 

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

"""
API for Feature Weighted Grid Statistics GDP requests.
"""

# Given a dataSetURI, makes a wps call to cida..., retrives the response XML and gets back
# a list of data types
def getDataType(dataSetURI, verbose=False):
    POST = WebProcessingService('http://cida.usgs.gov/climate/gdp/proxy/http://internal.cida.usgs.gov/gdp/utility/WebProcessingService', verbose=False)
    
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
    identifierElement.text = 'gov.usgs.cida.gdp.wps.algorithm.discovery.ListOpendapGrids'
    
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
    
    if not verbose:
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
    request = etree.tostring(root, pretty_print=False)
    execution = POST.execute(None, [], request=request)
    
    if not verbose:
        sys.stdout = old_stdout
        result_string = result.getvalue()
    return parseXMLatTag(execution.response, 'name')


# Given a datasetURI and a valid dataType, return
# the valid time range of the dataSet
def getDataSetTimeRange(dataSetURI, dataType, verbose=False):
    POST = WebProcessingService('http://cida.usgs.gov/climate/gdp/proxy/http://internal.cida.usgs.gov/gdp/utility/WebProcessingService', verbose=False)
    
    identifier = 'gov.usgs.cida.gdp.wps.algorithm.discovery.GetGridTimeRange'
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
    
    # <ows:Identifier>gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm</ows:Identifier>
    identifierElement = etree.SubElement(root, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = identifier
    
    # <wps:DataInputs>
    dataInputsElement = etree.SubElement(root, util.nspath_eval('wps:DataInputs', namespaces))
    inputElements = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
    identifierElement = etree.SubElement(inputElements, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'catalog-url'
    dataElement = etree.SubElement(inputElements, util.nspath_eval('wps:Data', namespaces))
    literalElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
    literalElement.text = dataSetURI
  
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
    
    responseFormElement = etree.SubElement(root, util.nspath_eval('wps:ResponseForm', namespaces))
    responseDocElement = etree.SubElement(responseFormElement, util.nspath_eval('wps:ResponseDocument', namespaces))
    outputElement = etree.SubElement(responseDocElement, util.nspath_eval('wps:Output', namespaces))
    identifierElement = etree.SubElement(outputElement, util.nspath_eval('ows:Identifier', namespaces))
    identifierElement.text = 'result'
    
    if not verbose:
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
    
    request = etree.tostring(root, pretty_print=True)
    execution = POST.execute(None, [], request=request)
    
    if not verbose:
        sys.stdout = old_stdout
        result_string = result.getvalue()
    return parseXMLatTag(execution.response, 'time')

# This should be a private method.
# Given an xml, searches for the tag, appends its text to a list
def parseXMLatTag(xml, tag):
   
    tag_text = []
    for node in xml.iter():
        if node.tag == tag:
            tag_text.append(node.text)
    return tag_text

def encodeZipFolder(zipfilePath):
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
    
    fileO = open(fileHandle, "r")
    stringData = fileO.read()
    fileO.close()
    
    filename = fileHandle.split("/")
    filename = filename[len(filename)-1] # will get the filename
    filename = filename.replace(".zip", "")
    wfsurl = 'http://cida-eros-gdp2.cr.usgs.gov:8082/geoserver'
    
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
    complexDataElement.text = stringData
    
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
    uploadRequest = etree.tostring(root, pretty_print=False)
    execution = POST.execute(None, [], request=uploadRequest)
    monitorExecution(execution)
    return filename

def getInput(listInput):
    
    for i in listInput:
        print i
    
    print '\n' + 'Choose from the list above:'
    usrinput = str(raw_input())
    while usrinput not in listInput:
        print 'not a valid input'
        usrinput = str(raw_input())
    return usrinput

def generateCapabilityURL(service_url):
    
    qs = []
    if service_url.find('?') != -1:
            qs = cgi.parse_qsl(service_url.split('?')[1])

    params = [x[0] for x in qs]

    if 'service' not in params:
        qs.append(('service', 'WFS'))
    if 'request' not in params:
        qs.append(('request', 'GetCapabilities'))
    if 'version' not in params:
        qs.append(('version', '1.1.0'))

    urlqs = urlencode(tuple(qs))
    return service_url.split('?')[0] + '?' + urlqs
    
def generateDescribeFeature(typename):
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
    
    urlen = generateDescribeFeature(shapefile)
    inputObject = urlopen(urlen)
    
    # lines contains the lines with attributes embedded in them
    lines = parseObjectforInfo(inputObject, 'xsd:element maxOccurs=')
    attributes = []
    
    # search the line
    for item in lines:
        word = getStringBetween('name=', item, ' ')
        # for attributes, will return "attribute", qoutes included, strip qoutes
        if word[1:len(word) - 1] != "the_geom":
            attributes.append(word[1: len(word) - 1])
    return attributes

def getStringBetween(beginterm, line, stopterm):
    
    begin_index = line.find(beginterm)
    end_index = line.find(stopterm, begin_index)
    
    return line[begin_index + len(beginterm) : end_index ]

def getAllStringBetweenInLine(beginterm, line, stopterm):
    
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
    # we are searching for attr-value, gml:id pair
    
    value = []
    tuple = []
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
            tuple.append(tmpTuple)
            
            tmpline = tmpline[end_index :]
            
            
            if valTerm not in value:
                value.append(valTerm)
            begin_index = end_index
            #print begin_index
        else:
            break
    return value, tuple

def generateValueFeature(typename, attribute):
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

def getValues(shapefile, attribute, getTuples='false'):
    
    urlen = generateValueFeature(shapefile, attribute)
    inputObject = urlopen(urlen)
    shapefileterm = shapefile.split(':')

    # inputObject for values had info only on lines[1]? (in all cases?) need to check
    lines = []
    for line in inputObject:
        lines.append(line)
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
    return getValues(shapefile, attribute, getTuples='only')
    
def getFilterID(tuples, value):
    
    filterID = []
    for item in tuples:
        if item[0] == value:
            filterID.append(item[1])
    return filterID

def parseObjectforInfo(inputObject, term):
    line_list = []
    for line in inputObject:
        if term in line:
            line_list.append(line)
    inputObject.close()
    return line_list

def filterSubOne(filterID):
    filter = filterID.split('.')
    no = int(filter[1])
    if (no - 1) < 1:
        return None
    filterID = filter[0] + '.' + str(no - 1)
    return filterID

def submitFeatureWeightedRequest(shpfile, dataSetURI, dataType, attribute, value, startTime, endTime, 
                                coverage='true', delim='COMMA', stat='MEAN', grpby='STATISTIC', timeStep='false', summAttr='false'):
    
    # I have an off by one error... eg the outputs are ID + 1
    filtersEdited = []
    tuples = getTuples(shpfile, attribute)
    filters = getFilterID(tuples, value)
    for f in filters:
        if filterSubOne(f) is not None:
            filtersEdited.append(filterSubOne(f))
    
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService')
    wfsUrl = 'http://cida-eros-gdp2.cr.usgs.gov:8082/geoserver/wfs'
    query = WFSQuery(shpfile, propertyNames=["the_geom", attribute], filters=filtersEdited)
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
    
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    
    execution = wps.execute(processid, inputs, output = "OUTPUT")
    monitorExecution(execution, download=True)    
    
    sys.stdout = old_stdout
    result_string = result.getvalue()
    
    output = result_string.split('\n')
    print output[len(output) - 3]
    print output[len(output) - 2]
    tmp = output[len(output) - 2].split(' ')
    fname = tmp[len(tmp)-1]
    
    return getData(fname, delim)
    

def getData(fname, delim):
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

# Submits an already well formed XML request to the WPS. Returns the dataset
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

def getAvailableFilesFromGeoServer():
    wfs = WebFeatureService(gdp_url)
    shapefiles = wfs.contents.keys()
    return shapefiles

# Gets a list of valid dataset URIs, currently hardcoded. WILL need to make CWS call
def getDataSetURI():
    dataSetURIs = ['http://regclim.coas.oregonstate.edu:8080/thredds/dodsC/regcmdata/NCEP/merged/monthly/RegCM3_A2_monthly_merged_NCEP.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/conus_grid.w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/maurer/maurer_brekke_w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/alaska_grid.w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/gmo/GMO_w_meta.ncml']
    return dataSetURIs
