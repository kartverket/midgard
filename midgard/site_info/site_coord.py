"""Site cooridnate information classes

Description:
------------
This module is divided into three different types of classes:

    1. Main class SiteCoord provides basic functionality to the user. See exampless
    2. Site coordinate source type classes:
        - There is one class for each source type.
        - A class with all relevant site coordinate information for a point in time.
    3. Site coordinate history source type classes:
        - There is one class for each source type.
        - Converts input from source_data to a object of type SiteCoordHistorySinex, etc and provides functions
          for accessing the history and relevant dates. 
        - The history consist of a time interval for which the entry is valid and an instance of a site coordinate 
          source type class for each defined time interval.

    If a source type does not contain information about the site coordinates the module will return 'None'.

Example:
--------
    
    from midgard import parsers
    from midgard.site_info.site_coord import SiteCoord
    from datetime import datetime

    # Read SINEX data    
    p = parsers.parse_file(parser_name='sinex_site', file_path='./data/site_info/igs.snx')
    source_data = p.as_dict()
    all_stations = source_data.keys()
    
    # Get station information
    SiteCoord.get("snx", "osls", datetime(2020, 1, 1), source_data, source_path=p.file_path)
    SiteCoord.get("snx", all_stations, datetime(2020, 1, 1), source_data, source_path=p.file_path)
    
    SiteCoord.get_history("snx", "osls", source_data, source_path=p.file_path)
    SiteCoord.get_history("snx", all_stations, source_data, source_path=p.file_path)

"""


# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union, Callable

# External library imports
import numpy as np

# Midgard imports
from midgard.data.position import Position
from midgard.data.time import Time
from midgard.dev.exceptions import MissingDataError
from midgard.site_info._site_info import SiteInfoBase, SiteInfoHistoryBase, ModuleBase

class SiteCoord(ModuleBase):
    """Main class for converting site coordinates from various sources into unified classes"""

    sources: Dict[str, Callable] = dict()

@SiteCoord.register_source
class SiteCoordHistorySinex(SiteInfoHistoryBase):

    source: str = "snx"
    
    def _process_history(
                self, 
                source_data: Dict,
    ) -> Dict[Tuple[datetime, datetime], "SiteCoordSinex"]:
        """Process site coordinate history from SINEX file

        Args:
            source_data:  Source data with site information.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are SiteCoordSinex objects.
        """
        if self.station not in source_data and self.station.upper() not in source_data:
            raise MissingDataError(f"Station {self.station!r} unknown in source '{self.source_path}'.")
        else:
            station = self.station if self.station in source_data else self.station.upper()
            if "solution_estimate" not in source_data[station]:
                # Site coordinates are not defined in this SINEX file
                return None
            else:
                raw_info = self._combine_sinex_block_data(source_data[station])
                return self._create_history(raw_info)

    @staticmethod
    def _combine_sinex_block_data(data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Combine SOLUTION/EPOCHS and SOLUTION/ESTIMATE SINEX block data to a common dictionary

        Args:
            data: Dictionary with SINEX file data for a station
        Return:
            List of dictionaries with station as keys and values with information from SOLUTION/EPOCHS 
            and SOLUTION/ESTIMATE SINEX block:
                
            Example:
                    
                [{'site_code': 'ABMF', 'point_code': 'A', 'soln': '1', 'obs_code': 'C', 
                  'start_epoch': datetime.datetime(2008, 10, 28, 0, 0),
                  'end_epoch': datetime.datetime(2009, 10, 15, 23, 59, 30),
                  'mean_epoch': datetime.datetime(2009, 4, 22, 11, 59, 45),
                  'STAX': {'param_idx': 1, 'param_name': 'STAX', 'site_code': 'ABMF', 'point_code': 'A', 'soln': '1',
                           'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 'unit': 'm', 'constraint': '2',
                           'estimate': 2919785.71307133, 'estimate_std': 0.00037297
                           },
                  'STAY': {...}
                  'STAZ': {...},
                  'VELX': {'param_idx': 4, 'param_name': 'VELX', 'site_code': 'ABMF', 'point_code': 'A', 'soln': '1',
                           'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 'unit': 'm/y', 'constraint': '2',
                           'estimate': 0.00751651888393245, 'estimate_std': 2.7261e-05
                          },
                  'VELY': {...},
                  'VELZ': {...}
                  },
                 {'site_code': 'ABMF', 'point_code': 'A', 'soln': '2', 'obs_code': 'C',
                  'start_epoch': datetime.datetime(2009, 10, 16, 0, 0),
                  'end_epoch': datetime.datetime(2012, 1, 24, 23, 59, 30),
                  'mean_epoch': datetime.datetime(2010, 12, 5, 11, 59, 45),
                  'STAX': {...},
                  'STAY': {...},
                  'STAZ': {...},
                  'VELX': {...},
                  'VELY': {...},
                  'VELZ': {...}
                  },
                 {'site_code': 'ABMF', 'point_code': 'A', 'soln': '3', 'obs_code': 'C',
                  'start_epoch': datetime.datetime(2012, 1, 25, 0, 0),
                  'end_epoch': datetime.datetime(2020, 4, 12, 0, 0),
                  'mean_epoch': datetime.datetime(2016, 3, 4, 0, 0),
                  'STAX': {...},
                  'STAY': {...},
                  'STAZ': {...},
                  'VELX': {...},
                  'VELY': {...},
                  'VELZ': {...}
                  }]
        """
        raw_info = list()

        if "solution_epochs" in data.keys():
            for idx, epoch in enumerate(data["solution_epochs"]):
                raw_info.append(epoch.copy())

                for estimate in data["solution_estimate"]:
                    if epoch["soln"] == estimate["soln"]:
                        raw_info[idx].update({estimate["param_name"]: estimate})
        return raw_info


    def _create_history(self, raw_info: List[Dict[str, Any]]) -> Dict[Tuple[datetime, datetime], "SiteCoordSinex"]:
        """Create dictionary of site coordinate history for station
        
        Args:
            raw_info: List of dictionaries with station as keys and values with information from SOLUTION/EPOCHS 
                      and SOLUTION/ESTIMATE SINEX block
                  
        Returns:
            dictionary with site coordinate history: keys: tuple(datetime, datetime), value: SiteCoordSinex object.
        """
        history = dict()
        for site_coord_info in raw_info:
            site_coord = SiteCoordSinex(self.station, site_coord_info)
            interval = (site_coord.date_from, site_coord.date_to)
            history[interval] = site_coord

        return history
     
        
    def set_history(self, raw_info: List[Dict[str, Any]]) -> None:
        """Set history station information
        
        Example 'raw_info':
            
                [{'site_code': 'ABMF', 'point_code': 'A', 'soln': '1', 'obs_code': 'C', 
                  'start_epoch': datetime.datetime(2008, 10, 28, 0, 0),
                  'end_epoch': datetime.datetime(2009, 10, 15, 23, 59, 30),
                  'mean_epoch': datetime.datetime(2009, 4, 22, 11, 59, 45),
                  'STAX': {'param_idx': 1, 'param_name': 'STAX', 'site_code': 'ABMF', 'point_code': 'A', 'soln': '1',
                           'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 'unit': 'm', 'constraint': '2',
                           'estimate': 2919785.71307133, 'estimate_std': 0.00037297
                           },
                  'STAY': {...}
                  'STAZ': {...},
                  'VELX': {'param_idx': 4, 'param_name': 'VELX', 'site_code': 'ABMF', 'point_code': 'A', 'soln': '1',
                           'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 'unit': 'm/y', 'constraint': '2',
                           'estimate': 0.00751651888393245, 'estimate_std': 2.7261e-05
                          },
                  'VELY': {...},
                  'VELZ': {...}
                  },
                 {'site_code': 'ABMF', 'point_code': 'A', 'soln': '2', 'obs_code': 'C',
                  'start_epoch': datetime.datetime(2009, 10, 16, 0, 0),
                  'end_epoch': datetime.datetime(2012, 1, 24, 23, 59, 30),
                  'mean_epoch': datetime.datetime(2010, 12, 5, 11, 59, 45),
                  'STAX': {...},
                  'STAY': {...},
                  'STAZ': {...},
                  'VELX': {...},
                  'VELY': {...},
                  'VELZ': {...}
                  },
                 {'site_code': 'ABMF', 'point_code': 'A', 'soln': '3', 'obs_code': 'C',
                  'start_epoch': datetime.datetime(2012, 1, 25, 0, 0),
                  'end_epoch': datetime.datetime(2020, 4, 12, 0, 0),
                  'mean_epoch': datetime.datetime(2016, 3, 4, 0, 0),
                  'STAX': {...},
                  'STAY': {...},
                  'STAZ': {...},
                  'VELX': {...},
                  'VELY': {...},
                  'VELZ': {...}
                  }]
        
        Args:
            raw_info: List of dictionaries with station as keys and values with information from SOLUTION/EPOCHS 
                      and SOLUTION/ESTIMATE SINEX block
        
        Attribute history attribute is set.
        """
        self.history = self._create_history(raw_info)


class SiteCoordSinex(SiteInfoBase):
    """ Site coordinate class handling SINEX file station coordinate information"""

    source: str = "snx"
    fields: Dict = dict()

    @property
    def date_from(self) -> datetime:
        """ Get site coordinate starting date from site information attribute

        Returns:
            Site coordinate starting date
        """
        if self._info["start_epoch"]:
            return self._info["start_epoch"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get site coordinate ending date from site information attribute

        Returns:
            Site coordinate ending date
        """
        if self._info["end_epoch"]:
            return self._info["end_epoch"]
        else:
            return datetime.max

    @property
    def pos(self) -> "TrsPosition":
        """ Get site coordinate from SINEX file

        Returns:
            Site coordinate
        """
        return Position(
                        val=[
                            self._info["STAX"]["estimate"],
                            self._info["STAY"]["estimate"],
                            self._info["STAZ"]["estimate"],
                        ],
                        system='trs',
        )

    @property
    def pos_sigma(self) -> np.ndarray:
        """ Get standard deviation of site coordinate from SINEX file

        Returns:
            Standard deviation of site coordinate for X, Y and Z in [m]
        """
        return np.array([
                        self._info["STAX"]["estimate_std"],
                        self._info["STAY"]["estimate_std"],
                        self._info["STAZ"]["estimate_std"],                
        ])

    @property
    def ref_epoch(self) -> "UtcTime":
        """ Get reference epoch of site coordinate from SINEX file

        Returns:
            Reference epoch of site coordinate
        """
        return Time(
                    val=self._info["STAX"]["ref_epoch"],
                    scale="utc",
                    fmt="datetime",
        )

    @property
    def system(self) -> str:
        """ Get reference system from site information attribute

        Returns:
            Reference system
        """
        return self._info["STAX"]["ref_system"] if "ref_system" in self._info["STAX"] else None

    @property
    def vel(self) -> np.ndarray:
        """ Get site velocity from SINEX file

        Returns:
            Site velocity for X, Y and Z component in [m/yr]
        """
        if "VELX" in self._info:
            if "estimate" in self._info["VELX"]:
                data = np.array([
                                self._info["VELX"]["estimate"],
                                self._info["VELY"]["estimate"],
                                self._info["VELZ"]["estimate"],                
                ])
            else:
                data = np.array([float('nan'), float('nan'), float('nan')])

        else:
            data = np.array([float('nan'), float('nan'), float('nan')])

        return data

    @property
    def vel_sigma(self) -> np.ndarray:
        """ Get standard deviation of site velocity from SINEX file

        Returns:
            Standard deviation of site velocity for X, Y and Z component in [m/yr]
        """
        if "VELX" in self._info:
            if "estimate_std" in self._info["VELX"]:
                data = np.array([
                                self._info["VELX"]["estimate_std"],
                                self._info["VELY"]["estimate_std"],
                                self._info["VELZ"]["estimate_std"],                
                ])
            else:
                data = np.array([float('nan'), float('nan'), float('nan')])

        else:
            data = np.array([float('nan'), float('nan'), float('nan')])

        return data


    #
    # SET METHODS
    #
    def set_date_from(self, date_from: datetime) -> None:
        """ Set site coordinate starting date in site information attribute

        Returns:
            date_from: Site coordinate starting date
        """
        self._info["start_epoch"] = date_from


    def set_date_to(self, date_to: datetime) -> None:
        """ Set site coordinate ending date in site information attribute

        Returns:
            date_to: Site coordinate ending date
        """
        self._info["end_epoch"] = date_to


    def set_system(self, system: str) -> None:
        """ Set reference system in site information attribute

        Args:
            system: Reference system
        """
        self._info["STAX"]["ref_system"] = system
        self._info["STAY"]["ref_system"] = system
        self._info["STAZ"]["ref_system"] = system


    def set_pos(self, pos: Union[List[float], np.ndarray]) -> None:
        """ Set site coordinate in site information attribute

        Args:
            pos: Site coordinates for X, Y and Z in [m]
        """
        self._info["STAX"]["estimate"] = pos[0]
        self._info["STAY"]["estimate"] = pos[1]
        self._info["STAZ"]["estimate"] = pos[2]


    def set_pos_sigma(self, pos_sigma: Union[List[float], np.ndarray]) -> None:
        """ Set standard deviation of site coordinate in site information attribute

        Args:
            pos_sigma: Standard deviation of site coordinate for X, Y and Z in [m]
        """
        self._info["STAX"]["estimate_std"] = pos_sigma[0]
        self._info["STAY"]["estimate_std"] = pos_sigma[1]
        self._info["STAZ"]["estimate_std"] = pos_sigma[2]                


    def set_ref_epoch(self, ref_epoch: datetime) -> None:
        """ Set reference epoch of site coordinate in site information attribute

        Args:
            ref_epoch: Reference epoch of site coordinate
        """
        self._info["STAX"]["ref_epoch"] = ref_epoch
        self._info["STAY"]["ref_epoch"] = ref_epoch
        self._info["STAZ"]["ref_epoch"] = ref_epoch


    def set_vel(self, vel: Union[List[float], np.ndarray]) -> None:
        """ Set site velocity in site information attribute

        Args:
            vel: Site velocity for X, Y and Z component in [m/yr]
        """
        self._info.setdefault("VELX", dict()).update(estimate=vel[0])
        self._info.setdefault("VELY", dict()).update(estimate=vel[1])
        self._info.setdefault("VELZ", dict()).update(estimate=vel[2])


    def set_vel_sigma(self, vel_sigma: Union[List[float], np.ndarray]) -> None:
        """ Set standard deviation of site velocity in site information attribute

        Args:
            vel_sigma: Standard deviation of site velocity for X, Y and Z component in [m/yr]
        """
        self._info.setdefault("VELX", dict()).update(estimate_std=vel_sigma[0])
        self._info.setdefault("VELY", dict()).update(estimate_std=vel_sigma[1])
        self._info.setdefault("VELZ", dict()).update(estimate_std=vel_sigma[2])


@SiteCoord.register_source
class SiteCoordHistorySsc(SiteInfoHistoryBase):

    source: str = "ssc"

    def _process_history(
                self, 
                source_data: Dict,
    ) -> Dict[Tuple[datetime, datetime], "SiteCoordSinex"]:
        """Process site coordinate history from SINEX file

        Args:
            source_data:  Source data with site information.

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are SiteCoordSsc objects.
        """
        if self.station in source_data:
            raw_info = source_data[self.station]
        elif self.station.upper() in source_data:
            raw_info = source_data[self.station.upper()]
        else:
            raise MissingDataError(f"Station '{self.station}' unknown in source '{self.source_path}'.")

        return self._create_history(raw_info)

    def _create_history(self, raw_info: Dict[str, Any]) -> Dict[Tuple[datetime, datetime], "SiteCoordSsc"]:
        """ Create site coordinate history from input dictionary
        
        Args:
            raw_info   dictionary with station information from ssc file
            
        Returns:
            dictionary with site coordinate history: keys: tuple(datetime, datetime), value: SiteCoord object.

        raw_info: Example of dictionary for a given station
        {'site_num': '10001', 'antenna_num': 'M007', 'name': 'SMNE', 'tech': 'GPS', 'antenna_id': 'SMNE', 'soln': 5,
         'pos_vel': {1: {'STAX': 4201791.972, 'STAY': 177945.561, 'STAZ': 4779286.951,
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2000, 11, 17, 0, 0), 
                         'end': datetime.datetime(2008, 4, 27, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001},
                     2: {'STAX': 4201791.982, 'STAY': 177945.564, 'STAZ': 4779286.96, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2008, 4, 29, 0, 0), 
                         'end': datetime.datetime(2009, 3, 10, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001},
                     3: {'STAX': 4201791.988, 'STAY': 177945.558, 'STAZ': 4779286.96, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2009, 3, 12, 0, 0), 
                         'end': datetime.datetime(2011, 4, 30, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001}, 
                     4: {'STAX': 4201791.977, 'STAY': 177945.564, 'STAZ': 4779286.955, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2011, 5, 8, 0, 0), 
                         'end': datetime.datetime(2015, 9, 29, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001}, 
                     5: {'STAX': 4201791.978, 'STAY': 177945.564, 'STAZ': 4779286.955, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2015, 10, 1, 0, 0), 
                         'end': datetime.datetime(2021, 2, 20, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001}
                    }
        }
        """
        history = dict()
        pos_vel = raw_info.pop("pos_vel")
        for site_coord_info in pos_vel.values():
            site_coord = SiteCoordSsc(self.station, site_coord_info)
            interval = (site_coord.date_from, site_coord.date_to)
            history[interval] = site_coord

        return history


    def set_history(self, raw_info: Dict[str, Any]) -> None:
        """Set history station information
        
        Example 'raw_info':

        {'site_num': '10001', 'antenna_num': 'M007', 'name': 'SMNE', 'tech': 'GPS', 'antenna_id': 'SMNE', 'soln': 5,
         'pos_vel': {1: {'STAX': 4201791.972, 'STAY': 177945.561, 'STAZ': 4779286.951,
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2000, 11, 17, 0, 0), 
                         'end': datetime.datetime(2008, 4, 27, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001},
                     2: {'STAX': 4201791.982, 'STAY': 177945.564, 'STAZ': 4779286.96, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2008, 4, 29, 0, 0), 
                         'end': datetime.datetime(2009, 3, 10, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001},
                     3: {'STAX': 4201791.988, 'STAY': 177945.558, 'STAZ': 4779286.96, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2009, 3, 12, 0, 0), 
                         'end': datetime.datetime(2011, 4, 30, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001}, 
                     4: {'STAX': 4201791.977, 'STAY': 177945.564, 'STAZ': 4779286.955, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2011, 5, 8, 0, 0), 
                         'end': datetime.datetime(2015, 9, 29, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001}, 
                     5: {'STAX': 4201791.978, 'STAY': 177945.564, 'STAZ': 4779286.955, 
                         'sigma_X': 0.001, 'sigma_Y': 0.001, 'sigma_Z': 0.001, 
                         'ref_epoch': datetime.datetime(2010, 1, 1, 0, 0), 
                         'start': datetime.datetime(2015, 10, 1, 0, 0), 
                         'end': datetime.datetime(2021, 2, 20, 23, 59, 30), 
                         'VELX': -0.013, 'VELY': 0.0175, 'VELZ': 0.0106, 
                         'sigma_VX': 0.0001, 'sigma_VY': 0.0001, 'sigma_VZ': 0.0001}
                    }
        }
        
        Args:
            raw_info: dictionary with station information from ssc file
        
        Attribute history attribute is set.
        """
        self.history = self._create_history(raw_info)


class SiteCoordSsc(SiteInfoBase):
    """ Site coordinate class handling SSC file station coordinate information
    """

    source: str = "ssc"
    fields: Dict = dict()


    #
    # GET METHODS
    #

    @property
    def date_from(self) -> datetime:
        """ Get site coordinate starting date from site information attribute

        Returns:
            Site coordinate starting date
        """
        if self._info["start"]:
            return self._info["start"]
        else:
            return datetime.min

    @property
    def date_to(self) -> datetime:
        """ Get site coordinate ending date from site information attribute

        Returns:
            Site coordinate ending date
        """
        if self._info["end"]:
            return self._info["end"]
        else:
            return datetime.max

    @property
    def pos(self) -> "TrsPosition":
        """ Get site coordinate from SSC file

        Returns:
            Site coordinate [m]
        """
        return Position(
                        val=[
                            self._info["STAX"],
                            self._info["STAY"],
                            self._info["STAZ"],
                        ],
                        system='trs',
        )

    @property
    def pos_sigma(self) -> np.ndarray:
        """ Get standard deviation of site coordinate from SCC file

        Returns:
            Standard deviation of site coordinate for X, Y and Z in [m]
        """
        return np.array([
                        self._info["sigma_x"],
                        self._info["sigma_y"],
                        self._info["sigma_z"],                
        ])

    @property
    def ref_epoch(self) -> "UtcTime":
        """ Get reference epoch of site coordinate from SINEX file

        Returns:
            Reference epoch of site coordinate
        """
        return Time(
                    val=self._info["ref_epoch"],
                    scale="utc",
                    fmt="datetime",
        )
        
    @property
    def system(self) -> str:
        """ Get reference system from site information attribute

        Returns:
            Reference system
        """
        return self._info["ref_system"] if "ref_system" in self._info else None

    @property
    def vel(self) -> np.ndarray:
        """ Get site velocity from SINEX file

        Returns:
            Site velocity for X, Y and Z component in [m/yr]
        """
        return np.array([
                        self._info["VELX"],
                        self._info["VELY"],
                        self._info["VELZ"],                
            ])

    @property
    def vel_sigma(self) -> np.ndarray:
        """ Get standard deviation of site velocity from SSC file

        Returns:
            Standard deviation of site velocity for X, Y and Z component in [m/yr]
        """
        return np.array([
                        self._info["sigma_VX"],
                        self._info["sigma_VY"],
                        self._info["sigma_VZ"],                
        ])


    #
    # SET METHODS
    #
    def set_date_from(self, date_from: datetime) -> None:
        """ Set site coordinate starting date in site information attribute

        Returns:
            date_from: Site coordinate starting date
        """
        self._info["start"] = date_from


    def set_date_to(self, date_to: datetime) -> None:
        """ Set site coordinate ending date in site information attribute

        Returns:
            date_to: Site coordinate ending date
        """
        self._info["end"] = date_to


    def set_system(self, system: str) -> None:
        """ Set reference system in site information attribute

        Args:
            system: Reference system
        """
        self._info["ref_system"] = system


    def set_pos(self, pos: Union[List[float], np.ndarray]) -> None:
        """ Set site coordinate in site information attribute

        Args:
            pos: Site coordinates for X, Y and Z in [m]
        """
        self._info["STAX"] = pos[0]
        self._info["STAY"] = pos[1]
        self._info["STAZ"] = pos[2]


    def set_pos_sigma(self, pos_sigma: Union[List[float], np.ndarray]) -> None:
        """ Set standard deviation of site coordinate in site information attribute

        Args:
            pos_sigma: Standard deviation of site coordinate for X, Y and Z in [m]
        """
        self._info["sigma_x"] = pos_sigma[0]
        self._info["sigma_y"] = pos_sigma[1]
        self._info["sigma_z"] = pos_sigma[2]                


    def set_ref_epoch(self, ref_epoch: datetime) -> None:
        """ Set reference epoch of site coordinate in site information attribute

        Args:
            ref_epoch: Reference epoch of site coordinate
        """
        self._info["ref_epoch"] = ref_epoch


    def set_vel(self, vel: Union[List[float], np.ndarray]) -> None:
        """ Set site velocity in site information attribute

        Args:
            vel: Site velocity for X, Y and Z component in [m/yr]
        """
        self._info["VELX"] = vel[0]
        self._info["VELY"] = vel[1]
        self._info["VELZ"] = vel[2]


    def set_vel_sigma(self, vel_sigma: Union[List[float], np.ndarray]) -> None:
        """ Set standard deviation of site velocity in site information attribute

        Args:
            vel_sigma: Standard deviation of site velocity for X, Y and Z component in [m/yr]
        """
        self._info["sigma_VX"] = vel_sigma[0]
        self._info["sigma_VY"] = vel_sigma[1]
        self._info["sigma_VZ"] = vel_sigma[2]


