# dependencies: lxml.etree, owslib
# =============================================================================
# Author : Xao Yang <xyang@usgs.gov>
#
# Contact email: xyang@usgs.gov
# =============================================================================
from owslib.wps import WebProcessingService, WFSFeatureCollection, WFSQuery, GMLMultiPolygonFeatureCollection, monitorExecution
from owslib.ows import DEFAULT_OWS_NAMESPACE, XSI_NAMESPACE, XLINK_NAMESPACE
from owslib.wfs import WebFeatureService
from owslib.etree import etree
from StringIO import StringIO
from urllib import urlencode
from urllib2 import urlopen
import owslib.util as util
import base64
import cgi
import sys
import os

#global urls for GDP and services
GDP_URL = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs' 
WFS_URL = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver/wfs'
upload_URL = 'http://cida-eros-gdp2.er.usgs.gov:8082/geoserver'
WPS_URL = 'http://cida.usgs.gov/gdp/process/WebProcessingService'
WPS_Service = 'http://cida.usgs.gov/gdp/utility/WebProcessingService'

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
CSW_NAMESPACE = 'http://www.opengis.net/cat/csw/2.0.2'

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
    'upload': UPLD_NAMESPACE,
    'csw': CSW_NAMESPACE
}

class gdpXMLGenerator():
    """
    This class is responsible for generating the upload XML tree template
    as well as the xml post request tree template.
    This class serves no other functions.
    """
    
    def _init_(self):
        pass
    
    def _subElement(self, root, elementName):
        return etree.SubElement(root, util.nspath_eval(elementName, namespaces))
    
    def getUploadXMLtree(self, filename, wfsUrl, filedata):
        
        # generate the POST XML request
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
        identifierElement = self._subElement(root, 'ows:Identifier')
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
        dataInputsElement = self._subElement(root,'wps:DataInputs')
        inputElements = self._subElement(dataInputsElement, 'wps:Input')
        identifierElement = self._subElement(inputElements, 'ows:Identifier')
        identifierElement.text = 'filename'
        
        dataElement = self._subElement(inputElements,'wps:Data')
        literalElement = self._subElement(dataElement, 'wps:LiteralData')
        literalElement.text = filename
        
        inputElements = self._subElement(dataInputsElement, 'wps:Input')
        identifierElement = self._subElement(inputElements, 'ows:Identifier')
        identifierElement.text = 'wfs-url'
        dataElement = self._subElement(inputElements,'wps:Data')
        literalElement = self._subElement(dataElement,'wps:LiteralData')
        literalElement.text = wfsUrl
    
        # adding complex information
        inputElements = self._subElement(dataInputsElement, 'wps:Input')
        identifierElement = self._subElement(inputElements, 'ows:Identifier')
        identifierElement.text = 'file'
        dataElement = self._subElement(inputElements, 'wps:Data')
        complexDataElement = etree.SubElement(dataElement, util.nspath_eval('wps:ComplexData', namespaces),
                                                  attrib={"mimeType":"application/x-zipped-shp", "encoding":"Base64"} )
        # sets filedata
        complexDataElement.text = filedata
        
        # <wps:ResponseForm>
        #    <wps:ResponseDocument>
        #        <ows:Output>
        #            <ows:Identifier>result</ows:Identifier>
        #        </ows:Output>
        #    </wps:ResponseDocument>
        # </wps:ResponseForm>
        responseFormElement = self._subElement(root, 'wps:ResponseForm')
        responseDocElement = self._subElement(responseFormElement, 'wps:ResponseDocument')
        outputElement = self._subElement(responseDocElement, 'wps:Output')
        identifierElement = self._subElement(outputElement, 'ows:Identifier')
        identifierElement.text = 'result'
        outputElement = self._subElement(responseDocElement, 'wps:Output')
        identifierElement = self._subElement(outputElement, 'ows:Identifier')
        identifierElement.text = 'wfs-url'
        outputElement = self._subElement(responseDocElement, 'wps:Output')
        identifierElement = self._subElement(outputElement,'ows:Identifier')
        identifierElement.text = 'featuretype'
        
        return root

    def getXMLRequestTree(self, dataSetURI, algorithm, method, varID=None, verbose=False):
        
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
            literalElement.text = varID
        
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
        
        return root
    
class pyGDPwebProcessing():
    """
    This class allows interactive calls to be made into the GDP.
    """
    
    def _init_(self, wfsUrl=WFS_URL, wpsUrl=WPS_URL, version='1.1.0'):
        self.wfsUrl = wfsUrl
        self.wpsUrl = wpsUrl
        self.version = version
        self.wps = WebProcessingService(wpsUrl)
        
    def WPSgetCapbilities(self, xml=None):
        """
        Returns a list of capabilities.
        """
        self.wps.getcapabilities(xml)
    def WPSdescribeprocess(self, identifier, xml=None):
        """
        Returns a list describing a specific identifier/process.
        """
        self.wps.describeprocess(identifier, xml)

    def _encodeZipFolder(self, filename):
        """
        This function will encode a zipfile and return the filename.
        """
        #check extension
        if not filename.endswith('.zip'):
            print 'Wrong filetype.'
            return
        
        #encode the file
        with open(filename, 'rb') as fin:
            bytesRead = fin.read()
            encode= base64.b64encode(bytesRead)
    
        #renames the file and saves it onto local drive
        filename = filename.split('.')
        filename = str(filename[0]) + '_copy.' + str(filename[-1])
        
        fout = open(filename, "w")
        fout.write(encode)
        fout.close()
        return filename

    def uploadShapeFile(self, filePath):
        """
        Given a file, this function encodes the file and uploads it onto geoserver.
        """
        
        # encodes the file, opens it, reads it, and closes it
        # returns a filename in form of: filename_copy.zip
        filePath = self._encodeZipFolder(filePath)
        if filePath is None:
            return
        
        filehandle = open(filePath, 'r')
        filedata = filehandle.read()
        filehandle.close()
        os.remove(filePath)  # deletes the encoded file
        
        # this if for naming the file on geoServer
        filename = filePath.split("/")
        # gets rid of filepath, keeps only filename eg: file.zip
        filename = filename[len(filename) - 1]
        filename = filename.replace("_copy.zip", "")
        
        
        # check to make sure a file with the same name does not exist
        fileCheckString = "upload:" + filename
        shapefiles = self.getShapefiles()
        if fileCheckString in shapefiles:
            print 'File exists already.'
            return
        
        xmlGen = gdpXMLGenerator()
        root = xmlGen.getUploadXMLtree(filename, upload_URL, filedata)
        
        # now we have a complete XML upload request
        uploadRequest = etree.tostring(root)
        POST = WebProcessingService(WPS_Service)
        execution = POST.execute(None, [], request=uploadRequest)
        monitorExecution(execution)
        return "upload:"+filename
    
    def getTuples(self, shapefile, attribute):
        """
        Will return the dictionary tuples only.
        """
        return self.getValues(shapefile, attribute, getTuples='only')
    
    def _getGMLIDString(self, GMLbeginterm, line, GMLstopterm, valBeginTerm, valStopTerm):
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
    
    def _urlen(self, typename):
        """
        Sets up a cgi request to the wfs for features specified.
        """
        
        service_url = GDP_URL
        
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
    
    def _getStringBetween(self, beginterm, line, stopterm):
        """
        Helper function. Gets the string between beginterm and stopterm. 
        Line is the line or superstring to be examined.
        returns the string inbetween.
        """
        
        begin_index = line.find(beginterm)
        end_index = line.find(stopterm, begin_index)
        
        return line[begin_index + len(beginterm) : end_index ]
        
    def _getLinesContaining(self, linesToParse, term):
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
    
    def _getFilterID(self,tuples, value):
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
    
    def _parseXMLNodesForTagText(self, xml, tag):
        """
        Parses through a XML tree for text associated with specified tag.
        Returns a list of the text.
        """
        
        tag_text = []
        for node in xml.iter():
            if node.tag == tag:
                tag_text.append(node.text)
        return tag_text
    
    def _generateRequest(self, dataSetURI, algorithm, method, varID=None, verbose=False):
        """
        Takes a dataset uri, algorithm, method, and datatype. This function will generate a simple XML document
        to make the request specified. (Only works for ListOpendapGrids and GetGridTimeRange). 
        
        Will return a list containing the info requested for (either data types or time range).
        """
        
        wps_Service = 'http://cida.usgs.gov/gdp/utility/WebProcessingService'
        POST = WebProcessingService(wps_Service, verbose=False)
        
        xmlGen = gdpXMLGenerator()
        root = xmlGen.getXMLRequestTree(dataSetURI, algorithm, method, varID, verbose)           
        
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
        return self._parseXMLNodesForTagText(execution.response, seekterm)
    
    def _generateFeatureRequest(self, typename, attribute=None):
        """
        This function, given a attribute and a typename or filename will return a list of values associated
        with the file and the attribute chosen.
        """
        
        service_url = GDP_URL
        qs = []
        if service_url.find('?') != -1:
                qs = cgi.parse_qsl(service_url.split('?')[1])
    
        params = [x[0] for x in qs]
    
        if 'service' not in params:
            qs.append(('service', 'WFS'))
        if 'request' not in params:
            if attribute is None:
                qs.append(('request', 'DescribeFeatureType'))
            else:
                qs.append(('request', 'GetFeature'))
        if 'version' not in params:
            qs.append(('version', '1.1.0'))
        if 'typename' not in params:
            qs.append(('typename', typename))
        if attribute is not None:
            if 'propertyname' not in params:
                qs.append(('propertyname', attribute))
            
        urlqs = urlencode(tuple(qs))
        return service_url.split('?')[0] + '?' + urlqs
    
    def getAttributes(self, shapefile):
        """
        Given a valid shapefile, this function will create a cgi call 
        returning a list of attributes associated with the shapefile.
        """
        # makes a call to get an xml document containing list of shapefiles
        urlen = self._generateFeatureRequest(shapefile)
        linesToParse = urlopen(urlen) 
        
        # gets back from the linesToParse document, all lines with 2nd arg
        lines = self._getLinesContaining(linesToParse, 'xsd:element maxOccurs=')
        attributes = []
        
        # search the line
        for item in lines:
            word = self._getStringBetween('name=', item, ' ')
            # for attributes, will return "attribute", qoutes included, strip qoutes
            if word[1:len(word) - 1] != "the_geom":
                attributes.append(word[1: len(word) - 1])
        return attributes
    
    def getShapefiles(self):
        """
        Returns a list of available files currently on geoserver.
        """
        wfs = WebFeatureService(GDP_URL)
        shapefiles = wfs.contents.keys()
        return shapefiles
    
    def getValues(self, shapefile, attribute, getTuples='false'):
        """
        Similar to get attributes, given a shapefile and a valid attribute this function
        will make a call to the Web Feature Services returning a list of values associated
        with the shapefile and attribute.
        
        If getTuples = True, will also return the tuples of [feature:id]  along with values [feature]
        """
        
        urlen = self._generateFeatureRequest(shapefile, attribute)
        inputObject = urlopen(urlen)
        shapefileterm = shapefile.split(':')
        
        strinx = inputObject.read()
        lines = strinx.split('\n')
        
        # gets the tag/namespace name
        stringSnippet = self._getStringBetween('<', lines[1], ':'+attribute+'>')
        stringSnippet = stringSnippet.split('<')
        shapefileterm[0] = stringSnippet[len(stringSnippet) - 1]
        
        # look for this pattern: <term[0]:attribute>SOUGHTWORD</term[0]:attribute>
        values, tuples = self._getGMLIDString('gml:id="', lines[1], '">', '<'+shapefileterm[0] + 
                                        ':' + attribute + '>', '</' +shapefileterm[0] +':' + 
                                        attribute + '>')
        if getTuples=='true':
            return sorted(values), sorted(tuples)
        elif getTuples=='only':
            return sorted(tuples)
        else:
            return sorted(values)
    
    def getDataType(self, dataSetURI, verbose=False):
        """
        Set up a get Data type request given a dataSetURI. Returns a list of all available data types.
        If verbose = True, will print on screen the waiting seq. for response document.
        """
            
        algorithm = 'gov.usgs.cida.gdp.wps.algorithm.discovery.ListOpendapGrids'
        return self._generateRequest(dataSetURI, algorithm, method='getDataType', varID=None, verbose=verbose)
        
        
        
    def getDataSetURI(self):
        """
        This function will not be implemented. This function is only implemented to give a few dataset URIs which may not work
        with certain datasets and will with others within the bounding box requirements.
        """ 
            
        print 'The dataSetURI outputs a select few URIs and may not work with the specific shapefile you are providing.'
        print 'To ensure compatibility, we recommend selecting a dataSetURI that is specific to the shapefile.' 
        print 'Or you may utilize the web gdp @ http://cida.usgs.gov/gdp/ to get a dataSet matching your specified shapefile.'
        print
            
        dataSetURIs = ['http://regclim.coas.oregonstate.edu:8080/thredds/dodsC/regcmdata/NCEP/merged/monthly/RegCM3_A2_monthly_merged_NCEP.ncml',
                           'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/conus_grid.w_meta.ncml',
                           'http://cida.usgs.gov/qa/thredds/dodsC/prism',
                           'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/maurer/maurer_brekke_w_meta.ncml',
                           'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/dcp/alaska_grid.w_meta.ncml',
                           'dods://igsarm-cida-thredds1.er.usgs.gov:8080/thredds/dodsC/gmo/GMO_w_meta.ncml']
        return dataSetURIs    
    
    def getGMLIDs(self, shapefile, attribute, value):
        """
        This function returns the gmlID associated with a particular attribute value.
        """
        tuples = self.getTuples(shapefile, attribute)
        return self._getFilterID(tuples, value)
    
    def getTimeRange(self, dataSetURI, varID, verbose=False):
        """
        Set up a get dataset time range request given a datatype and dataset uri. Returns the range
        of the earliest and latest time.
        If verbose = True, will print on screen the waiting seq. for response document.
        """
        
        algorithm = 'gov.usgs.cida.gdp.wps.algorithm.discovery.GetGridTimeRange'
        return self._generateRequest(dataSetURI, algorithm, method='getDataSetTime', varID=varID, verbose=verbose)
    
    
    def _getFeatureCollectionGeoType(self, geoType, attribute='the_geom', value=None, gmlIDs=None):
        """
        This function returns a featurecollection. It takes a geotype and determines if
        the geotype is a shapfile or polygon.
        """
        
        # This is a polygon
        if isinstance(geoType, list):
            return GMLMultiPolygonFeatureCollection( [geoType] )
        elif isinstance(geoType, str):
            if value==None and gmlIDs==None:
                print 'must input a value and attribute for shapefile'
                return
            else:
                tmpID = []
                if gmlIDs is None:
                    if type(value) == type(tmpID):
                        gmlIDs = []
                        for v in value:
                            tuples = self.getTuples(geoType, attribute)
                            tmpID = self._getFilterID(tuples, v)
                            gmlIDs = gmlIDs + tmpID
                    else:
                        tuples = self.getTuples(geoType, attribute)
                        gmlIDs = self._getFilterID(tuples, value)
                
                query = WFSQuery(geoType, propertyNames=["the_geom", attribute], filters=gmlIDs)
                return WFSFeatureCollection(WFS_URL, query)
        else:
            print 'Geotype is not a shapefile or a recognizable polygon.'
            return None
    
    def _executeRequest(self, processid, inputs, verbose):
        """
        This function makes a call to the Web Processing Service with
        the specified user inputs.
        """
        
        wps = WebProcessingService(WPS_URL)
        
        # if verbose=True, then will we will monitor the status of the call.
        # if verbose=False, then we will return only the file outputpath.
        if not verbose:
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
            
            #parses the redirected output to get the filepath of the saved file
            output = result_string.split('\n')
            tmp = output[len(output) - 2].split(' ')
            return tmp[len(tmp)-1]
    
        # executes the request
        execution = wps.execute(processid, inputs, output = "OUTPUT")
        monitorExecution(execution, download=True)   
    
    def submitFeatureWeightedGridStatistics(self, geoType, dataSetURI, varID, startTime, endTime, attribute='the_geom', value=None,
                                            gmlIDs=None, verbose=None, coverage='true', delim='COMMA', stat='MEAN', grpby='STATISTIC', 
                                            timeStep='false', summAttr='false'):
        """
        Makes a featureWeightedGridStatistics algorithm call. 
        """
        
        featureCollection = self._getFeatureCollectionGeoType(geoType, attribute, value, gmlIDs)
        if featureCollection is None:
            return
        
        processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
        inputs = [("FEATURE_ATTRIBUTE_NAME",attribute), 
                  ("DATASET_URI", dataSetURI), 
                  ("DATASET_ID", varID), 
                  ("TIME_START",startTime),
                  ("TIME_END",endTime), 
                  ("REQUIRE_FULL_COVERAGE",coverage), 
                  ("DELIMITER",delim), 
                  ("STATISTICS",stat), 
                  ("GROUP_BY", grpby),
                  ("SUMMARIZE_TIMESTEP", timeStep), 
                  ("SUMMARIZE_FEATURE_ATTRIBUTE",summAttr), 
                  ("FEATURE_COLLECTION", featureCollection)]
        
        return self._executeRequest(processid, inputs, verbose)
    
    def submitFeatureCoverageOPenDAP(self, geoType, dataSetURI, varID, startTime, endTime, attribute='the_geom', value=None, gmlIDs=None, 
                                     verbose=False, coverage='true'):
        """
        Makes a featureCoverageOPenDAP algorithm call. 
        """
        
        featureCollection = self._getFeatureCollectionGeoType(geoType, attribute, value, gmlIDs)
        if featureCollection is None:
            return
        processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageOPeNDAPIntersectionAlgorithm'
        inputs = [ ("DATASET_URI", dataSetURI),
                   ("DATASET_ID", varID), 
                   ("TIME_START",startTime), 
                   ("TIME_END",endTime),
                   ("REQUIRE_FULL_COVERAGE",coverage),
                   ("FEATURE_COLLECTION", featureCollection)]
        return self._executeRequest(processid, inputs, verbose)    

    def submitFeatureCoverageWCSIntersection(self, geoType, dataSetURI, varID, attribute='the_geom', value=None, gmlIDs=None, verbose=False, coverage='true'):
        """
        Makes a featureCoverageWCSIntersection algorithm call. 
        """
        
        featureCollection = self._getFeatureCollectionGeoType(geoType, attribute, value, gmlIDs)
        if featureCollection is None:
            return
        processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageIntersectionAlgorithm'
        inputs = [("DATASET_URI", dataSetURI),
                  ("DATASET_ID", varID),
                  ("REQUIRE_FULL_COVERAGE",coverage), 
                  ("FEATURE_COLLECTION", featureCollection)]
        return self._executeRequest(processid, inputs, verbose)
    
    def submitFeatureCategoricalGridCoverage(self, geoType, dataSetURI, varID, attribute='the_geom', value=None, gmlIDs=None, verbose=False,
                                             coverage='true', delim='COMMA'):
        """
        Makes a featureCategoricalGridCoverage algorithm call. 
        """
        
        featureCollection = self._getFeatureCollectionGeoType(geoType, attribute, value, gmlIDs)
        if featureCollection is None:
            return
        processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCategoricalGridCoverageAlgorithm'
        inputs = [ ("FEATURE_ATTRIBUTE_NAME",attribute),
               ("DATASET_URI", dataSetURI),
               ("DATASET_ID", varID),         
               ("DELIMITER", delim),
               ("REQUIRE_FULL_COVERAGE",coverage),
               ("FEATURE_COLLECTION", featureCollection)]
        return self._executeRequest(processid, inputs, verbose)