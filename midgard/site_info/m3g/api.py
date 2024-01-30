"""Python wrapper around the M3G API

Description:
------------
Creates functions automatically based on the services listed on the Swagger help page referred to by URL.

Note: Functionality for PUT endpoints is not implemented.

Example:
--------
from midgard.site_info import m3g

# Get instance of M3gApi class with API methods based on default URL
api = m3g.api.M3gApi()

# Get instance of M3gApi class with API methods based on defined URL
api = m3g.api.M3gApi(url=""https://gnss-metadata.eu/site/api-json")

"""

# Standard library imports
import pathlib
from typing import Any, Callable, Dict

# Third party imports
import requests


class M3gApi(object):
    """A wrapper around the M3G API
    """

    def __init__(self, url: str="https://gnss-metadata.eu/site/api-json") -> None:
        """Initialize API object

        Args:
            url: URL of open API docs
        """
        self.url = url
        url_root = self._get_url_root(url)

        # Get open api specification
        r = self._get_url(url)
        
        # Generate methods based on API help
        for path, info in r.json()["paths"].items():
            name = path.replace("/", "_").replace("-", "_")
            url_service = url_root + "/v1" + path                            
            
            for key in info.keys():
                if key == "put": #TODO: Functionality for PUT endpoints is not implemented.
                    continue
                doc = self._get_doc(info[key])              
                function_name = f"{key.lower()}{name}"
                #print(f"DEBUG: {path:40s} {function_name:70s}")
                content = self._get_content(info[key])
                setattr(self, function_name, self._api_factory(key, function_name, url_service, doc, content))
    
    #
    # AUXILIARY FUNCTIONS
    #            
    def _api_factory(self, type_, name: str, url: str, doc: str, content: str) -> Callable:
        """Create a function to read from the given URL

        Args:
            type_:    Type of request (delete, get, put)
            name:     Function name
            url:      M3G API URL, which should be wrapped
            doc:      M3G API help for given URL
            content:  Description of content of function

        Returns:
            Function for accessing M3G API
        """
        def api_function(to_json=True, **kwargs: Dict[str,str]) -> Dict:
            """Function that calls the API and returns a response
            
                to_json:     Enabled by default. Will try to convert response to json.
            """
            # Only get is open to everyone
            if type_ == "get":
                try:         
                    response = self._get_url(url, headers={"accept": ",".join(list(content.keys()))}, **kwargs)
                except KeyError as err:
                    raise TypeError(f"'{err.args[0]}' argument is missing")
                    
            #elif type_ == "put":
            #    try:
            #        response = self._put_url(url, headers={"accept": ",".join(list(content.keys()))}, **kwargs)
            #    except KeyError as err:
            #        raise TypeError(f"'{err.args[0]}' argument is missing")
            
            if to_json:
                try: #if response.text.startswith("[") or response.text.startswith("{"):
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    return response  # e.g. needed for getting text or binary (picture) files
            else:
                # Headers included
                return response
  
        # Update the api_function with proper names and docs
        api_function.__name__ = name
        api_function.__qualname__ = name
        api_function.__doc__ = doc
        
        return api_function
    
    def get_sitelog_all(self) -> Dict:
        """Get station metadata for all the stations in the API.
        
        The GET sitelog function usually returns "one page" of entries. This function loops through all the pages and collects
        all the entries into one list. Entries without sitelogs are skipped.
        
        Returns:
            Nested dictionary with all entries. Key is fourCharId. Secondary key is full station id.
            Example: {"ZIMM": {"ZIMM00CHE": {...<json from api>}}}

        """
        # Get first page
        sitelogs = dict()
        page = 1
        response = self.get_sitelog(to_json=False, page=page)
        page_count = int(response.headers["X-Pagination-Page-Count"])
        
        for entry in response.json():
            if entry["sitelog"]:
                sitelogs.setdefault(entry["sitelog"]["siteForm"]["fourCharId"], {}).update({entry['id']:entry})
                #sitelogs.setdefault(entry["id"], {}).update(entry)
        
        while page < page_count:
            page += 1
            response = self.get_sitelog(page=page)
            for entry in response:
                if entry["sitelog"]:
                    sitelogs.setdefault(entry["sitelog"]["siteForm"]["fourCharId"], {}).update({entry['id']:entry})
                    #sitelogs.setdefault(entry["id"], {}).update(entry)
        return sitelogs
           
        
    @staticmethod            
    def _error_message(url: str, response: Dict[str, Any]):
        """Generate error message based on request response
        
        Args:
            url:      Requested URL
            response: Response of request
        
        Returns:
            Error message
        """
        error_msg = ""
        if "message" in response:
            error_msg = f"{error_msg}\nMessage: {response['message']}"
            
        if "details" in response:
            error_msg = f"{error_msg}\nDetails: {response['details']}"
                  
        return f"Failure by URL {url} call\n{error_msg}"


    @staticmethod 
    def _get_content(info: Dict[str, Any]) -> Dict[str, Any]:
        """Get description of content of function
        
        Args:
            info: Dictionary with information about endpoint
                
        Returns:
            Content dictionary          
        """
        return info["responses"]["200"]["content"]
    

    @staticmethod 
    def _get_doc(info: Dict[str, Any]) -> str:
        """Get doc string of function
        
        TODO: Also function signature should be improved. See for example: https://stackoverflow.com/questions/1409295/set-function-signature-in-python
        
        Args:
            info: Dictionary with information about endpoint
                
        Returns:
            Doc string        
        """
        doc = info["summary"]
        if "parameters" in info.keys():
            doc = doc + "\n\nArgs:\n"
            for param in info["parameters"]:
                if "description" in param.keys():
                    doc = doc  + f"    {param['name']}:  {param['description']}\n"
                else:
                    doc = doc  + f"    {param['name']}:\n"

        return doc


    def _get_url(self, url: str, headers=None, **kwargs) -> requests.models.Response:
        """Check availability of URL and return GET request response object

        Args:
            url: URL path
            headers: set for get request
            kwargs: parameters for the url

        Returns:
            Request response object
        """
        try:
            for i, (k, v) in enumerate(kwargs.items()):
                symbol = "?" if i == 0 else "&"
                if isinstance(v, dict):
                    # k is filter: convert {"id": "like": "some_value"} to filter[id][like]=some_value
                    k1 = list(v.keys()).pop()
                    k2 = list(v[k1].keys()).pop()
                    url = f"{url}{symbol}{k}[{k1}][{k2}]={v[k1][k2]}"
                    if k != "filter":
                        print("warning: not implemented")
                else:
                    url = f"{url}{symbol}{k}={v}"
            
            if headers:
                response = requests.get(url, headers=headers)
            else:
                response = requests.get(url)
            response.raise_for_status()  # If the response was successful (status_code = 200), no exception will be raised.
            
        except requests.exceptions.RequestException as err: # all requests exceptions inherit from RequestException
            if not "response" in locals():
                raise ConnectionError(err)
            raise ValueError(self._error_message(url, response.json()))
            
        return response


    @staticmethod
    def _get_url_root(url: str) -> str:
        """Get root of URL path

        Args: 
            url: URL path
            
        Returns:
            Root of URL path
        """
        return "/".join(url.split("/")[0:3])
    
               
    def _put_url(self, url: str, json: Dict[str, Any]) -> requests.models.Response:
        """Check availability of URL and send PUT request to URL
    
        Args:
            url:      URL path
            json:     JSON data structure
            
        Returns:
            Request response object
        """
        try:
            response = requests.put(
                url=url,
                json= json,
            )
            response.raise_for_status()  # If the response was successful (status_code = 200), no exception will be raised.
    
        except requests.exceptions.RequestException as err: # all requests exceptions inherit from RequestException
            if not "response" in locals():
                raise ConnectionError(err)
            raise ValueError(self._error_message(url, response.json()))
            
        return response

