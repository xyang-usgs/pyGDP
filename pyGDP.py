# dependencies: lxml.etree, ows.lib and osgeo.ogr 
# =============================================================================
# Copyright (c) 2012 USGS
#
# Author : Xao Yang <xyang@usgs.gov>
#
# Contact email: xyang@usgs.gov
# =============================================================================
import lxml.etree as etree
import osgeo.ogr as ogr
from owslib.wps import WebProcessingService, WPSExecution, WFSFeatureCollection, WFSQuery, GMLMultiPolygonFeatureCollection, monitorExecution, printInputOutput
from owslib.ows import DEFAULT_OWS_NAMESPACE, XSI_NAMESPACE, XLINK_NAMESPACE, \
                       OWS_NAMESPACE_1_0_0, ServiceIdentification, ServiceProvider, OperationsMetadata
import owslib.util as util
import re, sys
from StringIO import StringIO

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



# Given a data source, returns the attributes from the shapefile
def getAttributesFromShape(filename):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(filename, 0)
    if dataSource is None:
        print 'Error with File. Retry.'
        return -1
    
    layer = dataSource.GetLayer()
    feature = layer.GetNextFeature()
    attributes = [feature.GetFieldDefnRef(i).GetName() for i in range(feature.GetFieldCount())]
    dataSource.Destroy()
    return attributes


# Given a shapefile and a corresponding attribute, return the 
# list of values associated with the attribute
def getValuesFromShape(filename, attribute):
    #resets feature reading
    """
    need to make sure dataSource.GetLayer works
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(filename, 0)
    if dataSource is None:
        print 'Error with File. Retry.'
        return -1
    
    layer = dataSource.GetLayer()
    feature = layer.GetNextFeature()
    value_list = []
    while feature:
        value = feature.GetFieldAsString(attribute)
        if value not in value_list:
            value_list.append(value)
        feature.Destroy()
        feature = layer.GetNextFeature()
    value_list = sorted(value_list) #sorts the values
    # resets the features
    layer.ResetReading()
    dataSource.Destroy()
    return value_list

# Given a valid value, attribute, and filename. We form 
# a gml off of the shapefile's geomtry.
def formGeometry(userValue, userAttribute, dataSource):
    
    layer = dataSource.GetLayer()
    feature = layer.GetNextFeature()
    geometry = []
    usrVal = []
    
    while feature:
        if type(userValue).__name__=='list':
            for i in userValue:
                if i == feature.GetFieldAsString(userAttribute):
                    geom = feature.GetGeometryRef()
                    geometry.append(geom.ExportToGML())
                    usrVal.append(i)
            feature.Destroy()
            feature = layer.GetNextFeature()
        else:
            if userValue == feature.GetFieldAsString(userAttribute):
                geom = feature.GetGeometryRef()
                geometry.append(geom.ExportToGML())
                usrVal.append(userValue)
            feature.Destroy()
            feature = layer.GetNextFeature()
    
    # tfile = open('rawGMLoutput.txt', 'w')
    # for i in geometry:
    #     tfile.write(str(i) + '\n')
    # tfile.close()
    
    return formGML(geometry, usrVal)

# Actual function that performs the task.
# Should be private.
def formGML(geometry, usrVal):
    geo_GML = []
    i = 0
    for g in geometry:
        # splits it to 3 parts:
        # begin tag, numbers, end tag
        gList = g.split("gml:coordinates>")
        one_feature = []
        for j in gList:
            #print j
            one_feature.append(j)
    
        coords = []
        tags = []
    
        k = 0
        while k < len(one_feature):
            tags.append(one_feature[k])
            k = k + 1
            if k < len(one_feature):
                coords.append(one_feature[k])
                k = k + 1
    
        # we now have the coords, in the right position
        s_coordinates = sortCoords(coords) 
        tags = adjustTags(tags)
        complete = []
        #put tags and coords together
        k = 0
        for k in range(len(one_feature) / 2):
            complete.append(tags[k])
            complete.append(s_coordinates[k])

        complete.append(tags[len(tags) - 1])        
        complete = "".join(complete)
        geo_GML.append([usrVal[i], complete])
        i = i + 1
        
    return geo_GML

# given a row of coords, fix their position
def sortCoord_I(coord):
    coord = coord.replace("</", "")
    sorted = coord.replace(",", " ")
    coordList = sorted.split(" ")
   
    i = 0
    while i < (len(coordList)):
        coordList[i], coordList[i + 1] = coordList[i + 1], coordList[i]
        i = i + 2
    
    updatedCoords = " ".join(coordList)
    return updatedCoords

# given a list of coordinates, fix position them
def sortCoords(coords):
    # now we have the coordinates
    sortedCoords = []
    for f in coords:
        sortedCoords.append(sortCoord_I(f))
    
    return sortedCoords

# adjusts the tags in the formation of gml/xml doc
def adjustTags(tags):
    
    tags[0] = tags[0].replace("outerBoundaryIs", "exterior")
    tags[0] = tags[0].replace("innerBoundaryIs", "interior")
    tags[0] = tags[0] + "gml:posList>" 
    
    i = 1
    while i < (len(tags) - 1):
        tags[i] = tags[i].replace("outerBoundaryIs", "exterior")
        tags[i] = tags[i].replace("innerBoundaryIs", "interior")
        tags[i] = "</gml:posList>" + tags[i]
        tags[i] = tags[i] + "gml:posList>"
        i = i + 1
        
    tags[(len(tags) - 1)] = tags[(len(tags) - 1)].replace("outerBoundaryIs", "exterior")
    tags[(len(tags) - 1)] = tags[(len(tags) - 1)].replace("innerBoundaryIs", "interior")
    tags[(len(tags) - 1)] = "</gml:posList>" + tags[(len(tags) - 1)] 
    
    return tags


# Gets a list of valid dataset URIs
def getDataSetURI():
    dataSetURIs = ['http://regclim.coas.oregonstate.edu:8080/thredds/dodsC/regcmdata/NCEP/merged/monthly/RegCM3_A2_monthly_merged_NCEP.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/conus_grid.w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/maurer/maurer_brekke_w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/alaska_grid.w_meta.ncml',
                   'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/gmo/GMO_w_meta.ncml']
    return dataSetURIs

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

# This should be a private method.
# Given an xml, searches for the tag, appends its text to a list
def parseXMLatTag(xml, tag):
   
    tag_text = []
    for node in xml.iter():
        if node.tag == tag:
            tag_text.append(node.text)
    return tag_text

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


# Takes an object with valid inputs, generates the corresponding XML 
# request and submits it against the WPS. Returns the dataset.
def submitFeatureWeightedRequest(filename, dataSetURI, dataType, attribute, value, start, end, coverage='true', delim='COMMA', stat='MEAN', stat2='COUNT', grpby='STATISTIC', timStp='false', fturat='false'):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(filename, 0)
    if dataSource is None:
        print 'Error with File. Retry.'
        return -1
    
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
    geom = formGeometry(value, attribute, dataSource)
    
    # tmpFile = open('tmpDebugGML.txt', 'w')
    # for i in geom:
    #    tmpFile.write(str(i)+'\n')
    # tmpFile.close()
    
    
    inputCollection = InputCollection(geom, attribute, value, start, end)
    inputs =  [ ("FEATURE_ATTRIBUTE_NAME",inputCollection.attribute),
           ("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataType),         
           ("TIME_START",inputCollection.start),
           ("TIME_END",inputCollection.end),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("DELIMITER",delim),
           ("STATISTICS",stat),
           ("STATISTICS", stat2),
           ("GROUP_BY",grpby),
           ("SUMMARIZE_TIMESTEP",timStp),
           ("SUMMARIZE_FEATURE_ATTRIBUTE",fturat),
           ("FEATURE_COLLECTION", inputCollection)
          ]

    execution = buildRequest(processid, inputs, output="OUTPUT")
    request = etree.tostring(execution, pretty_print = True)
    
    
    text_file = open("pyGDPoutputRequest.xml", "w")
    text_file.write(request)
    text_file.close()   
    
    
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService', verbose=False)
    execution = wps.execute(None, [], request=request)
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
    f = open(fname)
    rows = f.readlines()
    f.close()
    
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
    
def createFeatureWeightedInput(feature_atr_name, dataSetURI, dataSetID, Tstart, Tend, coverage='true', delim='TAB', stat='MEAN', stat2='COUNT', grpby='STATISTIC', timStp='false', fturat='false'):
    """
    Given the input information, generates a tuple list containing the proper inputs in the WPS
    returns the list
    """
    return [ ("FEATURE_ATTRIBUTE_NAME",feature_atr_name),
           ("DATASET_URI", dataSetURI),
           ("DATASET_ID", dataSetID),         
           ("TIME_START",Tstart),
           ("TIME_END",Tend),
           ("REQUIRE_FULL_COVERAGE",coverage),
           ("DELIMITER",delim),
           ("STATISTICS",stat),
           ("STATISTICS", stat2),
           ("GROUP_BY",grpby),
           ("SUMMARIZE_TIMESTEP",timStp),
           ("SUMMARIZE_FEATURE_ATTRIBUTE",fturat)
          ]


def submitFeatureWeightedQuery(filename, propertyNames, filters, wfsUrl, inputs):
    """
    filename: name of the file
    propertyName: the attributes of the file
    filters: the specific areas interested in
    wfsUrl: 
    inputs: list of input values consisting of the form:
        [ ("FEATURE_ATTRIBUTE_NAME","the_geom"),
           ("DATASET_URI", "dods://cida.usgs.gov/qa/thredds/dodsC/derivatives/derivative-days_above_threshold.pr.ncml"),
           ("DATASET_ID", "ensemble_b1_pr-days_above_threshold"),         
           ("TIME_START","2010-01-01T00:00:00.000Z"),
           ("TIME_END","2011-01-01T00:00:00.000Z"),
           ("REQUIRE_FULL_COVERAGE","false"),
           ("DELIMITER","TAB"),
           ("STATISTICS","MEAN"),
           ("STATISTICS", "COUNT"),
           ("GROUP_BY","STATISTIC"),
           ("SUMMARIZE_TIMESTEP","false"),
           ("SUMMARIZE_FEATURE_ATTRIBUTE","false"),
           ("FEATURE_COLLECTION", featureCollection)
          ]
    """
    wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService')
    
    query = (filename, propertyNames, filters)
    featureCollection = WFSFeatureCollection(wfsUrl, query)
    inputs.append(featureCollection)
    
    processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
    execution = wps.execute(processid, inputs, output="OUTPUT")
    return monitorExecution(execution)
    
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

def buildRequest(identifier, inputs=[], output=None):
    """
    builds the specific request XML
    returns the root node of the XML document
    """
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
        
    for input in inputs:
        key = input[0]
        val = input[1]
            
        inputElement = etree.SubElement(dataInputsElement, util.nspath_eval('wps:Input', namespaces))
        identifierElement = etree.SubElement(inputElement, util.nspath_eval('ows:Identifier', namespaces))
        identifierElement.text = key
            
            # Literal data
            # <wps:Input>
            #   <ows:Identifier>DATASET_URI</ows:Identifier>
            #   <wps:Data>
            #     <wps:LiteralData>dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/conus_grid.w_meta.ncml</wps:LiteralData>
            #   </wps:Data>
            # </wps:Input>
        if isinstance(val, str):
            dataElement = etree.SubElement(inputElement, util.nspath_eval('wps:Data', namespaces))
            literalDataElement = etree.SubElement(dataElement, util.nspath_eval('wps:LiteralData', namespaces))
            literalDataElement.text = val
                
            # Complex data
            # <wps:Input>
            #   <ows:Identifier>FEATURE_COLLECTION</ows:Identifier>
            #   <wps:Reference xlink:href="http://igsarm-cida-gdp2.er.usgs.gov:8082/geoserver/wfs">
            #      <wps:Body>
            #        <wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" service="WFS" version="1.1.0" outputFormat="text/xml; subtype=gml/3.1.1" xsi:schemaLocation="http://www.opengis.net/wfs ../wfs/1.1.0/WFS.xsd">
            #            <wfs:Query typeName="sample:CONUS_States">
            #                <wfs:PropertyName>the_geom</wfs:PropertyName>
            #                <wfs:PropertyName>STATE</wfs:PropertyName>
            #                <ogc:Filter>
            #                    <ogc:GmlObjectId gml:id="CONUS_States.508"/>
            #                </ogc:Filter>
            #            </wfs:Query>
            #        </wfs:GetFeature>
            #      </wps:Body>
            #   </wps:Reference>
            # </wps:Input>
        else:
            #inputElement.append( val.getXml() )
            dataElement = etree.SubElement(inputElement,util.nspath_eval('wps:Data', namespaces))
            complexDataElement = etree.SubElement(dataElement, util.nspath_eval('wps:ComplexData', namespaces), attrib={'schema': GML_SCHEMA_LOCATION, 'encoding':'UTF-8', 'mimeType': 'text/xml'})
            complexDataElement.append(val.constructFeatureCollection())
        
        # <wps:ResponseForm>
        #   <wps:ResponseDocument storeExecuteResponse="true" status="true">
        #     <wps:Output asReference="true">
        #       <ows:Identifier>OUTPUT</ows:Identifier>
        #     </wps:Output>
        #   </wps:ResponseDocument>
        # </wps:ResponseForm>
    if output is not None:
        responseFormElement = etree.SubElement(root, util.nspath_eval('wps:ResponseForm', namespaces))
        responseDocumentElement = etree.SubElement(responseFormElement, util.nspath_eval('wps:ResponseDocument', namespaces), 
                                                       attrib={'storeExecuteResponse':'true', 'status':'true'} )
        outputElement = etree.SubElement(responseDocumentElement, util.nspath_eval('wps:Output', namespaces), 
                                                       attrib={'asReference':'true'} )
        outputIdentifierElement = etree.SubElement(outputElement, util.nspath_eval('ows:Identifier', namespaces)).text = output
              
    return root

# OpenDap fuction. Submits request using opendap.
def submitOpenDapRequest(request):
    pass

#This class contains the input information as well as 
# a method to create the specific geometry GML that will be attached to 
# a XML request.
class InputCollection():
    """
    This class contains the input information as well as 
    a method to create the specific geometry GML that will be attached to 
    a XML request.
    """
    def __init__(self, geometryGML, attribute, value, start_time, end_time):
        
        self.geom = geometryGML
        self.attribute = attribute
        self.value = value
        self.start = start_time
        self.end  = end_time
    
    # Constructs a gml sheet off of the shapefile geometry. Returns the
    # GML/XML to be attached onto the XML request.
    def constructFeatureCollection(self): 
        """
        Constructs a gml sheet off of the shapefile geometry. Returns the
        GML/XML to be attached onto the XML request.
        """    
        root = etree.Element(util.nspath_eval('gml:featureMembers', namespaces), nsmap=namespaces,
                             attrib = { util.nspath_eval("xsi:schemaLocation",namespaces) : 'gov.usgs.cida.gdp.sample http://igsarm-cida-gdp1.er.usgs.gov:8080/sibley.xsd http://www.opengis.net/wfs http://igsarm-cida-gdp2.er.usgs.gov:8082/geoserver/schemas/wfs/1.1.0/wfs.xsd'})
        zz = 0
        # iterates through each specific polygon in the feature collection
        for geo in self.geom:
            sampleElement = etree.SubElement(root, util.nspath_eval('sample:CONUS_States', namespaces))
            sampleProp = etree.SubElement(sampleElement, util.nspath_eval('upload:the_geom', namespaces))
            upload = 'upload:'+str(self.attribute)
            sampleState = etree.SubElement(sampleElement, util.nspath_eval(upload, namespaces))
            # sampleState.text = self.value
            sampleState.text = geo[0]
        
            multiSurfaceElement = etree.SubElement(sampleProp, util.nspath_eval('gml:MultiSurface', namespaces), attrib={'srsName':'urn:x-ogc:def:crs:EPSG:4326', 'srsDimension': '2'})
            surfaceMemElement = etree.SubElement(multiSurfaceElement, util.nspath_eval('gml:surfaceMemeber', namespaces))
            
            eg = geo[1]
        
            eg = re.split('<|>', eg)
            for i in eg:
                if i == "":
                    eg.remove("")

            
            if eg[0].startswith('gml:Polygon'):
                shapeElement = etree.SubElement(surfaceMemElement, util.nspath_eval('gml:Polygon', namespaces))
            else:
                shapeElement = etree.SubElement(surfaceMemElement, util.nspath_eval(eg[0], namespaces))
            
            ind = 1
            while ind < len(eg):
                if eg[ind].startswith('gml'):
                    if eg[ind].startswith('gml:Polygon '):
                        tmpElement = etree.SubElement(shapeElement, util.nspath_eval('gml:Polygon', namespaces))
                    elif eg[ind].startswith('gml:exterior'):
                        tmpElement = etree.SubElement(shapeElement, util.nspath_eval(eg[ind], namespaces))  
                    elif eg[ind].startswith('gml:interior'):
                        tmpElement = etree.SubElement(shapeElement, util.nspath_eval(eg[ind], namespaces))  
                    else:    
                        tmpElement = etree.SubElement(tmpElement, util.nspath_eval(eg[ind], namespaces))  
                elif eg[ind] == "":
                    pass
                elif eg[ind].startswith('/gml'):
                    pass
                else:
                    tmpElement.text = eg[ind]
                ind = ind + 1

            
        return root
