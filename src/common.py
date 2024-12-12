from loguru import logger
import requests
import urllib
import uuid

TAB = "   "
def indent(level=0):
    return (TAB * level)

# Downloads a file from a specified URL 
# Returns status and the file contents
def fetch_file(url):
    status = False
    ret_value = ""
    header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '}

    logger.debug("Fetching: " + url)
    try:
        req = urllib.request.Request(url=url, headers=header)
        with urllib.request.urlopen(req) as response:
            ret_value = response.read()
        status = True
    except requests.exceptions.HTTPError as err:
        logger.error("The server returned an HTTP error.", str(err))
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        logger.error("TIMEOUT: The server took too long to respond.")
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        logger.error("Bad URL or too many redirects.")
    except requests.exceptions.RequestException as err:
        # catastrophic error.
        logger.error("Unable to fetch file.", str(err))
    except (Exception, BaseException) as error:
        logger.error("Problem downloading " + url, "(" + type(error).__name__ + ") " + str(error))

    if status:
        status = len(ret_value) > 0
        logger.debug("CONTENT TYPE: " + str(type(ret_value)))
        ret_value = normalize_content(ret_value)
        
    return ret_value

def get_file(file_name):
    ret_value = ""

    try:
        file = open(file_name, "rb")
        ret_value = file.read()
        file.close()
    except OSError:
        logger.debug("Could not open/read " + file_name)

    return ret_value

def normalize_content(content):
    ret_value = ""

    if isinstance(content, str):
        # ret_value = content.encode("utf-8") # convert to bytes
        # logger.debug ("Encode")
        logger.debug("Already string - do nothing")
    elif isinstance(content, bytes):
        ret_value = content.decode("utf-8")
        # logger.debug("Decode")
    else:
        logger.debug("Unhandled content encoding: " + type(content))

    return ret_value


def putfile(file_name, content):
    logger.debug("LFS Put File " + file_name)
    status = False
    try:
        with open(file_name, mode='w') as file:
            file.write(content)
            file.close()
        status = True
    except (Exception, BaseException) as error:
        logger.error("Error saving file to local FS " + file_name + "(" + type(error).__name__ + ") " + str(error))

    return status


def uuid_format(uuid_suffix=None):
    ret_value = ""
    if uuid_suffix is None:
        ret_value = uuid.uuid4()
    else:
        ret_value = "11111111-2222-4000-8000-"+ "{:012d}".format(uuid_suffix)

    return ret_value 

