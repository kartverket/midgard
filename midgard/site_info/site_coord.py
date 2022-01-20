""" Site coordinate information classes

Description:
------------
The site_coord module generates a SiteCoord object based on site information from 
the SINEX file or other sources.

Following steps are carried out for getting a SiteCoord object:

    1. Plugins modulen register SiteInfoHistory classes (e.g. 
       SiteCoordHistorySinex) and updates the 'sources' attribute of the 
       SiteInfoHistory class. 
    2. The SiteCoord object is initialized by calling the SiteCoord.get function. 
    3. The SiteInfoHistory.get function is called via the SiteCoord.get function.
       Here the correct SiteInfoHistory class is choosen by accessing the 
       registered 'sources' attribute of the SiteInfoHistory class.
    4. The SiteInfoBase.get function reads the antenna information via the
       _read_history() function of the SiteInfoHistorySinex or other 
       calls. The antenna information is selected via a given date. 


Example:
--------
    
    from midgard.site_info import site_coord; from datetime import datetime
    site_coord.SiteCoord.get(source="sinex", station="zimm", date=datetime(2018, 10, 1), source_path="igs.snx") 
"""


# Standard library imports
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

# External library imports
import numpy as np

# Midgard imports
from midgard import parsers
from midgard.data.position import Position
from midgard.data.time import Time
from midgard.dev import log
from midgard.site_info._site_info import SiteInfoBase, SiteInfoHistory, SiteInfoHistoryBase 


class SiteCoord():
    """Main site coordinate class for getting site coordinate object depending on site information source

    The site information source can be e.g. a SINEX file.
    """

    sources = dict()

    @classmethod
    def get(
            cls, 
            source: str, 
            station: str, 
            date: datetime, 
            source_path: Union[None, str] = None,
            source_data: Union[None, Any] = None,
    ) -> Union["SiteCoordSinex", Any]:
        """Get site coordinate object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            date:         Date for getting site information
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.

        Returns:
            Site coordinate object 
        """
        history = SiteInfoHistory.get(__name__, source, station, source_path, source_data)
        return history.get(date)

    @classmethod
    def get_history(
            cls, 
            source: str, 
            station: str, 
            source_path: Union[None, str] = None,
            source_data: Union[None, Any] = None,
    ) -> Union["SiteCoordSinex", Any]:
        """Get site coordinate history object depending on given source

        Args:
            source:       Site information source e.g. 'sinex' (SINEX file)
            station:      Station name.
            source_path:  Source path of site information source (e.g. file path of SINEX file)
            source_data:  Source data with site information. If source data are defined, then 'source_path' is 
                          ignored.

        Returns:
            Site coordinate object 
        """
        history = SiteInfoHistory.get(__name__, source, station, source_path, source_data)
        return history


@SiteInfoHistory.register_source
class SiteCoordHistorySinex(SiteInfoHistoryBase):

    source = "sinex"

    def _read_history(
                self, 
                source_data: Union[None, Any] = None,
    ) -> Dict[Tuple[datetime, datetime], "SiteCoordSinex"]:
        """Read site coordinate history from SINEX file

        Args:
            source_data:  Source data with site information. If source data are defined, then data are not read
                          from 'source_path'.            

        Returns:
            Dictionary with (date_from, date_to) tuple as key. The values are SiteCoordSinex objects.
        """

        # Get SINEX file data by reading from file 'source_path'
        if not source_data:
            if self.source_path is None:
                log.fatal("No SINEX file path is defined.")

            # Find site_id and read antenna history
            p = parsers.parse_file("sinex_site", file_path=self.source_path)
            source_data = p.as_dict()

        if self.station in source_data:
            raw_info = self._combine_sinex_block_data(source_data[self.station])
        elif self.station.upper() in source_data:
            raw_info = self._combine_sinex_block_data(source_data[self.station.upper()])
        else:
            raise ValueError(f"Station '{self.station}' unknown in source '{self.source_path}'.")

        # Create list of site coordinate history
        history = dict()
        for site_coord_info in raw_info:
            site_coord = SiteCoordSinex(self.station, site_coord_info)
            interval = (site_coord.date_from, site_coord.date_to)
            history[interval] = site_coord

        return history


    @staticmethod
    def _combine_sinex_block_data(data: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Combine SOLUTION/EPOCHS and SOLUTION/ESTIMATE SINEX block data to a common dictionary

        Args:
            data: SINEX file data for a station

        Return:
            Dictionary with station as keys and values with information from SOLUTION/EPOCHS and SOLUTION/ESTIMATE SINEX 
            block
        """
        raw_info = list()

        if "solution_epochs" in data.keys():
            for idx, epoch in enumerate(data["solution_epochs"]):
                raw_info.append(epoch.copy())

                for estimate in data["solution_estimate"]:
                    if epoch["soln"] == estimate["soln"]:
                        raw_info[idx].update({estimate["param_name"]: estimate})

        return raw_info


class SiteCoordSinex(SiteInfoBase):
    """ Site coordinate class handling SINEX file station coordinate information
    """

    source = "sinex"
    fields = dict()


    #
    # GET METHODS
    #

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
            return datetime.max - timedelta(days=367)  # TODO: Minus 367 days is necessary because
            #       _year2days(cls, year, scale) in ./midgard/data/_time.py
            #      does not work. Exceeding of datetime limit 9999 12 31.

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
    def ref_epoch(self) -> "Time":
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


