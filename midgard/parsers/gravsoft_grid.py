"""A parser for reading GRAVSOFT grid text files

Description:
------------
GRAVSOFT grid data are stored rowwise from north to south. The grid values are initiated with label of latitude (lat) and longitude (lon) limits and spacing followed by the data section like:

    lat1 lat2 lon1 lon2 dlat dlon
 
    dn1  dn2 ... dnm
    ...
    ...
    d11  d12 ... d1m 
 
The grid label defines the exact latitude and longitude of the grid points with:

    lat1: west boundary of latitude
    lat2: east boundary of latitude
    lon1: west boundary of longitude
    lon2: east boundary of longitude
    dlat: latitude grid spacing
    dlon: longitude grid spacing
    
The first data value in a grid file is thus the NW-corner (lat2, lon1) and the last the SE-corner (lat1, lon2). The number of points in a grid file is thus:

    num_lat = (lat2 - lat1)/dlat + 1
    num_lon = (lon2 - lon1)/dlon + 1
    
Unknown data are shown by 9999.

More information about the GRAVSOFT grid format can be found under:

Forsberg, R. and Tscherning, C. C. (2014): "An overview manual for the GRAVSOFT Geodetic Gravity Field Modelling 
Programs", 3. edition, August 2014

Example:
--------

    from midgard import parsers

    p = parsers.parse_file(parser_name="gravsoft_grid",  file_path="MeanSeaLevel1996-2014_above_Ellipsoid_EUREF89_v2021a.bin")
    data = p.as_dict()
    

"""
# Standard library imports
from typing import Any, Dict

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import log
from midgard.dev import plugins
from midgard.files import files
from midgard.parsers import Parser


@plugins.register
class GravsoftGrid(Parser):
    """A parser for reading GRAVSOFT grid text files

    Following **data** are available after reading data:

    | Parameter           | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | griddata            | Grid data with ordered grid blocks as list                                            |

    and **meta**-data:

    | Key                 | Description                                                                           |
    |---------------------|---------------------------------------------------------------------------------------|
    | grid_increment_lat  | Latitude grid increment in degree                                                     |
    | grid_increment_lon  | Longitude grid increment in degree                                                    |
    | grid_lat_max        | Maximal latitude border limit of grid area in degree                                  |
    | grid_lat_max        | Maximal latitude border limit of grid area in degree                                  |
    | grid_lat_min        | Minimal latitude border limit of grid area in degree                                  |
    | grid_lon_max        | Maximal longitude border limit of grid area in degree                                 |
    | grid_lon_min        | Minimal longitude border limit of grid area in degree                                 |
    | __data_path__       | File path                                                                             |
    | __parser_name__     | Parser name                                                                           |
    """
    
    #TODO: Can the reading also be handled of setup_parser() by using LineParser
    def _not_used_setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # Parse header
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+-
        #     57.000000   72.000000    4.000000   32.000000   0.0050000   0.0100000
        self._parse_header()
        
        # Parse data
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+-
        #   9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999
        #   9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999
        #   9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999
        return dict(
            skip_header=2,
            autostrip=True,
        )

    def read_data(self) -> None:
        """Read grid data from GRAVSOFT text file"""
   
        # Parse header
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+-
        #     57.000000   72.000000    4.000000   32.000000   0.0050000   0.0100000
        self._parse_header()
        

        # Parse data
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+-
        #   9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999
        #   9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999
        #   9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999 9999.999
        with files.open(self.file_path, mode="r") as fid:
            for num_line, line in enumerate(fid):
                if len(line) > 1 and num_line != 0: # Skip empty lines and first line
                    self.data.setdefault("griddata", list()).extend(line.split())
                    
    def _parse_header(self) -> None:
        """Parse header
        """
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: # TODO: Read only one line. Better solution as loop.
                lat_min, lat_max, lon_min, lon_max, dlat, dlon = line.split()
                self.meta["grid_lat_min"] = float(lat_min)
                self.meta["grid_lat_max"] = float(lat_max)
                self.meta["grid_lon_min"] = float(lon_min)
                self.meta["grid_lon_max"] = float(lon_max)
                self.meta["grid_increment_lat"] = float(dlat)
                self.meta["grid_increment_lon"] = float(dlon)
                break

    #
    # GET DICTIONARY
    #                    
    def as_dict(self) -> Dict[str, Any]:
        """Return the parsed data as a dictionary

        Returns:
            Dictionary with following entries:
            

           | Key        | Type              | Description                                                  |
           |------------|-------------------|--------------------------------------------------------------|
           | data       | numpy.ndarray     | Grid data of dimension (longitude x latitude)                |
           | latitude   | numpy.ndarray     | Latitude values of grid in degree                            |
           | longitude  | numpy.ndarray     | Longitude values of grid in degree                           |
           
           If no data are available an empty dictionary is returned.
        """
        if not self.data:
            return dict()
        
        num_grid_lon = int(round((self.meta["grid_lon_max"] - self.meta["grid_lon_min"]) / self.meta["grid_increment_lon"], 1) + 1)
        num_grid_lat = int(round((self.meta["grid_lat_max"] - self.meta["grid_lat_min"]) / self.meta["grid_increment_lat"], 1) + 1)

        lon = np.linspace(
                    self.meta["grid_lon_min"],
                    self.meta["grid_lon_max"],
                    num_grid_lon,
                    endpoint=True,
        )
        lat = np.linspace(
                    self.meta["grid_lat_max"],
                    self.meta["grid_lat_min"],
                    num_grid_lat,
                    endpoint=True,
        )
        
        if len(self.data["griddata"]) != num_grid_lon * num_grid_lat:
            log.fatal("Wrong dimensions.")

        data = np.array(self.data["griddata"]).astype(float)
        #import IPython; IPython.embed()
        data = data.reshape(num_grid_lat, num_grid_lon)

        return dict(
                longitude = lon, 
                latitude = lat, 
                data = data,
        )
        
            


