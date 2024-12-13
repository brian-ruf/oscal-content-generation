from loguru import logger
from saxonche import *
# from lxml import etree as ET
import elementpath
from elementpath.xpath3 import XPath3Parser
from xml.etree import ElementTree
from xml.dom import minidom
from common import *

log_level = "DEBUG"
new_level = logger.level("DATABASE", no=38, color="<blue>")
# log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS zz}</green> | <level>{level: <8}</level> | <yellow>Line {line: >4} ({file}):</yellow> <b>{message}</b>"
logger.add("logs/app_{time}.log", level=log_level, rotation="5 MB", retention="12 hours", enqueue=True)
logger.debug("Start")

OSCAL_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/1.0"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# OSCAL CLASS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class oscal:
    """
OSCAL Class

Properties:
- content: The string representing the content as originally passed to the class
- valid_xml: A boolean indicating whether the content was found to be well-formed XML
- xml_namespace: The identified default namespace
- valid_oscal: A boolean indicating whether the content was found to OSCAL schema valid
  - Currently, valid just means a recognized OSCAL model name (root) and OSCAL version (/metadata/oscal-veraion)
- oscal_format: The recognized OSCAL format ("xml", "json" or "yaml")
  - Currently, the value will only be XML as the class only accepts XML. 
  - Phase 3: Accept all three formats
- oscal_version: The value in the /metadata/oscal-version field
- oscal_model: The OSCAL model name exatly as it appears in OSCAL syntax
  ["catalog", "profile", "component-definition", "system-security-plan", "assessment-plan", "assessment-results", "plan-of-action-and-milestones"]
- doc: The lxml representation of the content
    """
    def __init__(self, content):
        self.content = content
        self.valid_xml = False
        self.xml_namespace = ""
        self.valid_oscal = False
        self.oscal_format = ""
        self.oscal_version = ""
        self.oscal_model = ""
        self.tree = None
        self.nsmap = {"": OSCAL_DEFAULT_NAMESPACE}
        self.__saxon = None

        # check for XML validity
        try:
            self.tree = ElementTree.fromstring(content.encode('utf_8'))
            self.valid_xml = True
        except ElementTree.XMLSyntaxError as e:
            logger.debug("CONTENT DOES NOT APPEAR TO BE VALID XML")
            for entry in e.error_log:
                    logger.error(f"Error: {entry.message} (Line: {entry.line}, Column: {entry.column})")


        if self.valid_xml:
            logger.debug("Content appears to be well-formed XML")
            logger.debug(self.tree.tag)
            root_element = self.xpath_atomic("/*/name()")
            logger.debug("ROOT ELEMENT: " + str(root_element))
            if root_element in ["catalog", "profile", "component-definition", "system-security-plan", "assessment-plan", "assessment-results", "plan-of-action-and-milestones"]:
                logger.debug("OSCAL ROOT ELEMENT DETECTED: " + root_element)
                self.oscal_version = self.xpath_atomic("//metadata/oscal-version/text()")
                logger.debug("OSCAL_VERSION: " + str(self.oscal_version))
                if len(self.oscal_version) >= 5: # TODO: Look up value in list of known-valid OSCAL versions
                    self.OSCAL_validate()
            else:
                logger.error("ROOT ELEMENT IS NOT AN OSCAL MODEL: " + root_element)



    def OSCAL_validate(self):
        """
        Currently does nothing.
        Will soon validate OSCAL XML content using the appropriate NIST OLSCAL XML Schema file for the specified OSCAL model and version.
        Eventually will use metaschema definitions to validate.
        """
        self.valid_oscal = True
        pass


    def OSCAL_convert(self, directive):
        """
        Currently does nothing. Will soon accept the following directive values:
        'xml-to-json'
        'xml-to-yaml'
        """
        pass

    def __setup_saxon(self): # Future - place holder for code for now
        self.__saxon = PySaxonProcessor(license=False)
        try: 
            self.xdm = self.__saxon.parse_xml(xml_text=content)
            # self.__saxon.declare_namespace("", "http://csrc.nist.gov/ns/oscal/1.0")
            self.valid = True
            self.oscal_format = "xml"
        except:
            logger.error("Content does not appear to be valid XML. Unable to rpoceed")

        if self.valid:
            self.xp = self.__saxon.new_xpath_processor() # Instantiates XPath processing
            self.handle_ns()
            self.xp.set_context(xdm_item=self.xdm) # Sets xpath processing context as the whole file
            temp_ret = self.xpath_global("/*/name()")
            if temp_ret is not None:
                self.root_node = temp_ret[0].get_atomic_value().string_value
                logger.debug("ROOT: " + self.root_node)
            self.oscal_version = self.xpath_global_single("/*/*:metadata/*:oscal-version/text()")
            logger.debug("OSCAL VERSION: " + self.oscal_version)

    def __saxon_serializer(self):
        return self.xdm.to_string('utf_8')


    def __saxon_handle_ns(self):
        node_ = self.xdm
        child = node_.children[0]
        assert child is not None
        namespaces = child.axis_nodes(8)

        for ns in namespaces:
            uri_str = ns.string_value
            ns_prefix = ns.name

            if ns_prefix is not None:
                logger.debug("xmlns:" + ns_prefix + "='" + uri_str + "'")
            else:
                logger.debug("xmlns uri=" + uri_str + "'")
                # set default ns here
                self.xp.declare_namespace("", uri_str)


    def __saxon_xpath_global(self, expression):
        ret_value = None
        logger.debug("Global Evaluating: " + expression)
        ret = self.xp.evaluate(expression)
        if  isinstance(ret,PyXdmValue):
            logger.debug("--Return Size: " + str(ret.size))
            ret_value = ret
        else:
            logger.debug("--No result")

        return ret_value

    def __saxon_xpath_global_single(self, expression):
        ret_value = ""
        logger.debug("Global Evaluating Single: " + expression)
        ret = self.xp.evaluate_single(expression)
        if  isinstance(ret, PyXdmValue): # isinstance(ret,PyXdmNode):
            ret_value = ret.string_value
        else:
            logger.debug("--No result")
            logger.debug("TYPE: " + str(type(ret)))

        return ret_value


    def __saxon_xpath(self, context, expression):
        ret_value = None
        logger.debug("Evaluating: " + expression)
        xp = self.__saxon.new_xpath_processor() # Instantiates XPath processing
        xp.set_context(xdm_item=context)
        ret = xp.evaluate(expression)
        if  isinstance(ret,PyXdmValue):
            logger.debug("--Return Size: " + str(ret.size))
            ret_value = ret
        else:
            logger.debug("--No result")

        return ret_value

    def __saxon_xpath_single(self, context, expression):
        ret_value = ""
        logger.debug("Evaluating Single: " + expression)
        xp = self.__saxon.new_xpath_processor() # Instantiates XPath processing
        xp.set_context(xdm_item=context)
        ret = xp.evaluate_single(expression)
        if  isinstance(ret, PyXdmValue): # isinstance(ret,PyXdmNode):
            ret_value = ret.string_value
        else:
            logger.debug("--No result")
            logger.debug("TYPE: " + str(type(ret)))

        return ret_value
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    
    def xpath_atomic(self, xExpr, context=None):
        ret_value=""
        if context is None:
            logger.debug("XPath [1]: " + xExpr)
            ret_value = elementpath.select(self.tree, xExpr, namespaces=self.nsmap)[0]
        else:
            logger.debug("XPath [1] (" + context.tag + "): " + xExpr)
            ret_value = elementpath.select(context, xExpr, namespaces=self.nsmap)[0]

        return str(ret_value)

    def xpath(self, xExpr, context=None):
        """
        Performs an xpath query either on the entire XML document 
        or on a context within the document.

        Parameters:
        - xExpr (str): An xpath expression
        - context (obj)[optional]: Context object.
        If the context object is present, the xpath expression is run against
        that context. If absent, the xpath expression is run against the 
        entire document.

        Returns: 
        - None if there is an error or if nothing is found.
        - 
        """
        
        ret_value=None
        if context is None:
            logger.debug("XPath [1]: " + xExpr)
            ret_value = elementpath.select(self.tree, xExpr, namespaces=self.nsmap)
        else:
            logger.debug("XPath [1] (" + context.tag + "): " + xExpr)
            ret_value = elementpath.select(context, xExpr, namespaces=self.nsmap)
        logger.debug(str(type(ret_value)))
        return ret_value

    def serializer(self):
        logger.debug("Serializing for Output")
        ElementTree.indent(self.tree)
        out_string = ElementTree.tostring(self.tree, 'utf-8')
        logger.debug("LEN: " + str(len(out_string)))
        out_string = normalize_content(out_string)
        out_string = out_string.replace("ns0:", "")
        out_string = out_string.replace(":ns0", "")
        
        return out_string
    
    def lookup(self, xExpr: str, attributes: list=[], children: list=[]):
        """
        Checks for the existence of an element basedon an xpath expression.
        Returns a dict containing any of the following if available: id, uuid, title
        If aditional attributes or children are specified in the function call
        and found to be present, they are included in the dict as well. 
        Parameters:
        - xExpr (str): xpath expression. This should always evaluate to 0 or 1 nodes
        - attributes(list)[Optional]: a list of additional attributes to return
        - children(list)[Optional]: a list of additional children to return

        Return:
        - dict or None
        dict = {
           {'attribute/field name', 'value'},
           {'attribute/field name', 'value'}        
        }
        """
        ret_value = None
        target_node = self.xpath(xExpr)
        if target_node:
            ret_value = {}
            if 'id' in target_node.attrib:
                ret_value.append({"id", target_node.get("id")})
            if 'uuid' in target_node.attrib:
                ret_value.append({"uuid", target_node.get("uuid")})

            title = target_node.find('./title', self.nsmap)
            if title:
                ret_value.append({"title", title.text})

            for attribute in attributes:
                ret_value.append({attribute, target_node.get(attribute)})

            for child in children:
                child_node = target_node.find('./' + child, self.nsmap)
                if child_node:
                    ret_value.append({child, child_node.text})


        return ret_value

    def append_child(self, xpath, node_name, node_content = None, attribute_list = []):
        # logger.debug("APPENDING " + node_name + " as child to " + xpath) #  + " in " + self.tree.tag)
        status = False
        try:
            parent_node = self.tree.find(xpath, namespaces=self.nsmap)
            # parent_node = self.xpath(xpath)
            logger.debug(parent_node)
            if parent_node is not None:
                logger.debug("TAG: " + parent_node.tag)
                child = ElementTree.Element(node_name)

                if node_content is str:
                    child.text = node_content

                for attrib in attribute_list:
                    child.set(attrib[0], attrib[1])

                parent_node.append(child)
                status = True
            else:
                logger.warning("APPEND: Unable to find " + xpath )
        except (Exception, BaseException) as error:
            logger.error("Error appending child (" + node_name + "): " + type(error).__name__ + " - " + str(error))
        
        if status:
            return child
        else:
            return None

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def append_params(control_obj, implemented_requirement, catalog_obj):

    logger.debug("Looking for Params")
    params = catalog_obj.xpath("./param", control_obj)
    # params = control_obj.find("./param", namespaces=nsmap)
    if params is not None:
        logger.debug("PARAMS FOUND: " + str(len(params)))
        for param in params:
            param_response = ElementTree.Element("set-parameter")
            param_response.set("param-id", param.get("id"))
            param_value = ElementTree.Element("value")
            param_value.text = "placeholder"
            param_response.append(param_value)
            implemented_requirement.append(param_response)


def append_response_points(control_obj, implemented_requirement, catalog_obj, statement_uuid):
    uuid_statement_incr = 100
    uuid_component_incr = 1
    rp_expansion = "./part[@name='statement']//prop[@name='response-point' and @ns='https://fedramp.gov/ns/oscal']/../@id"
    logger.debug("Looking for Response Points")
    r_points = catalog_obj.xpath(rp_expansion, control_obj)
    logger.debug(r_points)
    if r_points is not None:
        logger.debug("RPs FOUND: " + str(len(r_points)))
        for rp in r_points:
            statement = ElementTree.Element("statement")
            statement.set("statement-id", rp)
            statement.set("uuid", uuid_format(statement_uuid))
            append_by_component(statement, statement_uuid + uuid_component_incr, 
                                "11111111-2222-4000-8000-009000000000", 
                                "This is the 'this-system' component that must be present for every statement")
            implemented_requirement.append(statement)
            statement_uuid += uuid_statement_incr


def append_by_component(statement, by_component_uuid, component_uuid, content=""):

    by_component = ElementTree.Element("by-component")
    by_component.set("component-uuid", component_uuid)
    by_component.set("uuid", uuid_format(by_component_uuid))
    description = ElementTree.Element("description")
    paragraph = ElementTree.Element("p")
    paragraph.text = content
    description.append(paragraph)
    by_component.append(description)
    statement.append(by_component)


def process_components(by_component_uuid): # catalog_obj, xpath_expression, control_uuid):
    comp_out = ""
    uuid_component_incr = 1

    by_component_uuid += uuid_component_incr
    comp_out += indent(4) + "<by-component component-uuid='11111111-2222-4000-8000-009000000000' uuid='" + uuid_format(by_component_uuid) + "'>\n"
    comp_out += indent(5) + "<description><p>This is the 'this-system' component.</p></description>\n"
    comp_out += indent(5) + "<implementation-status state='operational' />\n"
    comp_out += indent(4) + "</by-component>\n"

    return comp_out


def insert_controls(catalog_obj, ssp_obj):
    logger.debug("Inserting Controls ...")
    limit = 5
    limit_cntr = 0
    ssp_control_output = ""
    uuid_cntr=12000000000
    uuid_control_incr = 10000
    status = False

    xpath_expression = "//control"
    controls = catalog_obj.xpath(xpath_expression)
    if controls is not None: # isinstance(controls,PyXdmValue):
        logger.debug("SIZE: " + str(len(controls)))
        for control_obj in controls:
            uuid_cntr += uuid_control_incr
            control_id = (catalog_obj.xpath_atomic("./@id", context=control_obj)).strip()
            if control_id not in ["ac-1", "ac-2"]:
                logger.debug("CONTROL: " + control_id)
                attributes = [["control-id", control_id], ["uuid", uuid_format(uuid_cntr)]]
                implemented_requirement = ssp_obj.append_child("control-implementation" , "implemented-requirement", node_content = None, attribute_list = attributes)

                if implemented_requirement is not None:
                    append_params(control_obj, implemented_requirement, catalog_obj)
                    append_response_points(control_obj, implemented_requirement, catalog_obj, uuid_cntr)

                    status = True
            else:
                logger.debug("Skipping  " + control_id)
            # ssp_control_output += process_response_points(catalog_obj, xpath_expression + "[@id='" + control_id + "']" + rp_expansion, uuid_cntr)

            limit_cntr += 1
            if limit_cntr > limit: break

    else:
        logger.debug("TYPE: " + str(type(controls)))

    return status

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

catalog_url = "https://raw.githubusercontent.com/GSA/fedramp-automation/refs/heads/develop/dist/content/rev5/baselines/xml/FedRAMP_rev5_HIGH-baseline-resolved-profile_catalog.xml"
ssp_base_file = "./fedramp-ssp-example_base.oscal.xml"
ssp_complete_file = "./fedramp-ssp-example.oscal.xml"
ssp_control_output = ""

catalog_content = fetch_file(catalog_url)
catalog_obj = oscal(catalog_content)
ssp_content = normalize_content(get_file(ssp_base_file))
ssp_obj = oscal(ssp_content)

if catalog_obj.valid_oscal:
    if ssp_obj.valid_oscal:
        if insert_controls(catalog_obj, ssp_obj):
            output = ssp_obj.serializer()
            logger.debug(str(type(output)))
            putfile(ssp_complete_file, output)
        else: 
            logger.error("Problem inserting controls. No file created.")
    else:
        logger.error("Problem loading base SSP")
else:
    logger.error("problem loading catalog.")


