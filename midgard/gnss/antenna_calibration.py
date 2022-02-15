"""Handling of GNSS antenna calibration information based on ANTEX file

Description:
------------

The module includes a class for handling of GNSS antenna information based on read GNSS ANTEX file (see Rothacher, 2010).


Reference:
----------

Rothacher, M. and Schmid, R. (2010): "ANTEX: The antenna exchange format", version 1.4, Forschungseinrichtung 
        Satellitengeodäsie, TU München
        
        
Example:
--------

# Import AntennaCalibration class
from midgard.gnss.antenna_calibration import AntennaCalibration

# Get instance of AntennaCalibration class by defining ANTEX file path 
ant = AntennaCalibration(file_path="igs14.atx")

"""
# Standard library imports
import datetime
from pathlib import Path, PosixPath
from typing import List, Dict, Union
from warnings import warn

# External library imports
import numpy as np

# Migard imports
from midgard import parsers
from midgard.collections import enums
from midgard.dev import log
from midgard.dev import plugins


@plugins.register
class AntennaCalibration():
    """A class for representing GNSS antenna calibration data

    The attribute "data" is a dictionary with GNSS satellite PRN or receiver antenna as key. The GNSS satellite antenna
    corrections are time dependent and saved with "valid from" datetime object entry. The dictionary looks like:

        dout = { <prn> : { <valid from>: { cospar_id:   <value>,
                                           sat_code:    <value>,
                                           sat_type:    <value>,
                                           valid_until: <value>,
                                           azimuth:     <list with azimuth values>,
                                           elevation:   <list with elevation values>,
                                           <frequency>: { azi: [<list with azimuth-elevation dependent corrections>],
                                                          neu: [north, east, up],
                                                          noazi: [<list with elevation dependent corrections>] }}},

                 <receiver antenna> : { azimuth:     <list with azimuth values>,
                                        elevation:   <list with elevation values>,
                                        <frequency>: { azi: [<array with azimuth-elevation dependent corrections>],
                                                       neu: [north, east, up],
                                                       noazi: [<list with elevation dependent corrections>] }}}

    with following entries:

    | Value              | Type              | Description                                                             |
    |--------------------|---------------------------------------------------------------------------------------------|
    | azi                | numpy.ndarray     | Array with azimuth-elevation dependent antenna correction in [mm] with  |
    |                    |                   | the shape: number of azimuth values x number of elevation values.       |
    | azimuth            | numpy.ndarray     | List with azimuth values in [rad] corresponding to antenna corrections  |
    |                    |                   | given in `azi`.                                                         |
    | cospar_id          | str               | COSPAR ID <yyyy-xxxa>: yyyy -> year when the satellite was put in       |
    |                    |                   | orbit, xxx -> sequential satellite number for that year, a -> alpha     |
    |                    |                   | numeric sequence number within a launch                                 |
    | elevation          | numpy.ndarray     | List with elevation values in [rad] corresponding to antenna            |
    |                    |                   | corrections given in `azi` or `noazi`.                                  |
    | <frequency>        | str               | Frequency identifier (e.g. G01 - GPS L1)                                |
    | neu                | list              | North, East and Up eccentricities in [m]. The eccentricities of the     |
    |                    |                   | mean antenna phase center is given relative to the antenna reference    |
    |                    |                   | point (ARP) for receiver antennas or to the center of mass of the       |
    |                    |                   | satellite in X-, Y- and Z-direction.                                    |
    | noazi              | numpy.ndarray     | List with elevation dependent (non-azimuth-dependent) antenna           |
    |                    |                   | correction in [mm].                                                     |
    | <prn>              | str               | Satellite code e.g. GPS PRN, GLONASS slot or Galileo SVID number        |
    | <receiver antenna> | str               | Receiver antenna name together with radome code                         |
    | sat_code           | str               | Satellite code e.g. GPS SVN, GLONASS number or Galileo GSAT number      |
    | sat_type           | str               | Satellite type (e.g. BLOCK IIA)                                         |
    | valid_from         | datetime.datetime | Start of validity period of satellite in GPS time                       |
    | valid_until        | datetime.datetime | End of validity period of satellite in GPS time                         |


    Attributes:
        data (dict):           Data read from GNSS Antenna Exchange (ANTEX) file
        file_path (str):       ANTEX file path

    Methods:
        satellite_phase_center_offset(): Determine satellite phase center offset correction vectors given in ITRS
        satellite_type(): Get satellite type from ANTEX file (e.g. BLOCK IIF, GALILEO-1, GALILEO-2, GLONASS-M,
                          BEIDOU-2G, ...)
        _used_date(): Choose correct date for use of satellite antenna corrections
    """

    def __init__(self, file_path: Union[str, PosixPath]) -> None:
        """Set up a new GNSS antenna calibration object by parsing ANTEX file

        The parsing is done by `midgard.parsers.antex.py` parser.
        
        Args:
            file_path: File path of ANTEX file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError(f"File {file_path} does not exists.")
            
        p = parsers.parse_file(parser_name="antex", file_path=file_path)
        if not p.data_available:
            raise ValueError(f"No observations in file {file_path}.")

        self.data = p.as_dict()
        self.file_path = p.file_path

    
    def get_pco_rcv(
            self, 
            system: str,
            frequency: str,
            antenna: str,
            radome: str = "NONE",
    ) -> Union[None, List[float]]:
        """Get antenna PCO of receiver in topocentric (local) reference system

        Args:
            system:     GNSS identifier (e.g. E=Galileo, G=GPS, ...)
            frequency:  GNSS frequency related to given 'system' argument (e.g. E1, E5a, L1)
            antenna:    Antenna type of receiver.
            radome:     4-digit radome type name of antenna

        Returns:
            Antenna PCO of receiver in topocentric (local) reference system or None if no entries could be found
        """
        antex_freq = self._gnss_to_antex_freq(system,frequency)
        if antex_freq is None:
            return None
        
        antenna_type = f"{antenna:15s} {radome}"
        if antenna_type not in self.data.keys():
            raise ValueError(f"Antenna type {antenna_type!r} is not available in ANTEX file {self.file_path}.")
            return None
        
        if antex_freq not in self.data[antenna_type].keys():
            frequencies = set(self.data[antenna_type].keys()) - {"azimuth", "elevation"}
            raise ValueError(f"Frequency {system}:{frequency} (ANTEX: {antex_freq}) is not available for antenna "
                      f"{antenna_type!r} in ANTEX file {self.file_path}. Following ANTEX frequencies are " 
                      f"available: {', '.join(frequencies)})")
            return None
    
        # Get antenna phase center offset (PCO) of receiver given in topocentric (local) reference system
        pco_rcv = self.data[antenna_type][antex_freq]["neu"]

        log.debug(f"PCO of receiver antenna {antenna_type!r} for frequency {system}:{frequency}: {pco_rcv}.")

        return pco_rcv


    def get_pco_sat(
            self, 
            date: Union[datetime.datetime, datetime.date],
            system: str,
            frequency: Union[str, List[str]],
            satellite: str, 
    ) -> Union[None, List[float]]:
        """Get satellite PCO in satellite reference system

        If two frequencies are given over the 'sys_freq' argument, then the PCOs are determined as an ionospheric linear
        combination.

        Args:
            date:       Given date used for finding corresponding satellite PCOs in ANTEX file
            system:     GNSS identifier (e.g. E=Galileo, G=GPS, ...)
            frequency:  GNSS frequency related to given 'system' argument, which can be a single frequency (e.g. E1) or a frequency combination (e.g. E1, E5a)
            satellite:  Satellite identifier.

        Returns:
            Satellite PCO in satellite reference system or None if no entries could be found
        """
        frequency = [frequency] if type(frequency) == str else frequency  # Convert str to list type
 
        # Get used date
        used_date = self._used_date(date, satellite)
        if used_date is None:
            return None
        
        antex_freq_1 = self._gnss_to_antex_freq(system, frequency[0])
        if antex_freq_1 is None:
            return None

        # Get satellite PCO for one frequency
        if len(frequency) == 1:

            # Get satellite phase center offset (PCO) given in satellite reference system
            pco_sat = np.array(self.data[satellite][used_date][antex_freq_1]["neu"])

            log.debug(f"PCO of satellite {satellite} for frequency {system}:{frequency[0]}: {pco_sat}.")

        # Get satellite PCO for ionospheric-free linear combination based on two-frequencies
        elif len(frequency) == 2:
            
            antex_freq_2 = self._gnss_to_antex_freq(system, frequency[1])
            if antex_freq_2 is None:
                return None

            # Coefficient of ionospheric-free linear combination
            f1 = getattr(enums, "gnss_freq_" + system)[frequency[0]]  # Frequency of 1st band
            f2 = getattr(enums, "gnss_freq_" + system)[frequency[1]]  # Frequency of 2nd band
            n = f1 ** 2 / (f1 ** 2 - f2 ** 2)
            m = -f2 ** 2 / (f1 ** 2 - f2 ** 2)

            # Get satellite phase center offset (PCO) given in satellite reference system
            pco_sat_f1 = np.array(self.data[satellite][used_date][antex_freq_1]["neu"])
            pco_sat_f2 = np.array(self.data[satellite][used_date][antex_freq_2]["neu"])

            # Generate ionospheric-free linear combination
            pco_sat = n * pco_sat_f1 + m * pco_sat_f2

            log.debug(
                f"Ionospheric-free linear combination PCOs of satellite {satellite} for frequency combination "
                f"{system}:{frequency[0]}_{frequency[1]}:  {pco_sat}."
            )

        else:
            raise ValueError(
                f"Wrong frequency type '{system}:{'_'.join(frequency)}'. Only single or dual frequencies can be handled."
            )

        return list(pco_sat)


    def get_satellite_info(
            self,
            date: Union[datetime.datetime, datetime.date],
            satellite: str, 
    ) -> Dict[str, str]:
        """Get satellite information for a given date

        Args:
            sat:   Satellite identifier.
            date:  Date.

        Returns:
            Satellite information
        """
        if satellite not in self.data.keys():
            raise ValueError(
                f"Satellite '{satellite}' is not given in ANTEX file {self.file_path}."
            )

        used_date = self._used_date(date, satellite)

        return {
            "sat_type": self.data[satellite][used_date]["sat_type"],
            "sat_code": self.data[satellite][used_date]["sat_code"],
            "cospar_id": self.data[satellite][used_date]["cospar_id"],
        }
    
    
    def get_satellite_type(
            self, 
            date: Union[datetime.datetime, datetime.date], 
            satellite: Union[str, List[str], np.ndarray],
    ) -> List[str]:
        """Get satellite type from ANTEX file (e.g. BLOCK IIF, GALILEO-1, GALILEO-2, GLONASS-M, BEIDOU-2G, ...)

        Args:
            date:       Date for which satellite PCOs should be collected
            satellite:  Array with satellite numbers 

        Returns:
            Satellite type information

        """
        satellite = np.array([satellite]) if type(satellite) is str else np.array(satellite)
        num_obs = satellite.shape[0]
        sat_types = np.zeros(num_obs, dtype=object)

        # Loop over all satellites given in RINEX observation file and configuration file
        for sat in set(satellite):

            # Skip satellites, which are not given in ANTEX file
            if sat not in self.data:
                warn(
                    f"Satellite {sat!r} is not given in ANTEX file {self.file_path}."
                )
                continue

            # Get array with information about, when observation are available for the given satellite (indicated
            # by True)
            idx = satellite == sat

            # Get used date
            used_date = self._used_date(date, sat)
            if used_date is None:
                continue

            # Get satellite type
            sat_type = self.data[sat][used_date]["sat_type"]
            sat_types[idx] = sat_type

        return list(sat_types)


    #
    # AUXILIARY FUNCTIONS
    #
    @staticmethod
    def _freq_num_to_freq_name(system: str, freq_num: str) -> Union[None, str]:
        """Get GNSS frequency name based on frequency band number L<num>/C<num> related to RINEX definition
 
        Args: 
            system:    GNSS identifier (e.g. E=Galileo, G=GPS, ...)
            freq_num:  Frequency band number L<num>/C<num> related to RINEX definition
            
        Returns:
            GNSS frequency name
        """
        
        # GNSS          Freq number      GNSS freq
        #               L<num>/C<num>
        # ___________________________________________
        # C (BeiDou):   2                'B1'
        #               7                'B2'
        #               6                'B3'
        # G (GPS):      1                'L1'
        #               2                'L2'
        #               5                'L5'
        # R (GLONASS):  1                'G1'
        #               2                'G2'
        #               3                'G3'
        # E (Galileo):  1                'E1'
        #               8                'E5 (E5a+E5b)'
        #               5                'E5a'
        #               7                'E5b'
        #               6                'E6'
        # I (IRNSS):    5                'L5'
        #               9                'S'
        # J (QZSS):     1                'L1'
        #               2                'L2'
        #               5                'L5'
        #               6                'LEX'
        # S (SBAS):     1                'L1'
        #               5                'L5'
        freq_num_to_freq_name = {
            "C": {"2": "B1", "7": "B2", "6": "B3"},
            "E": {"1": "E1", "8": "E5", "5": "E5a", "7": "E5b", "6": "E6"},
            "G": {"1": "L1", "2": "L2", "5": "L5"},
            "I": {"5": "L5", "9": "S"},
            "J": {"1": "L1", "2": "L2", "5": "L5", "6": "LEX"},
            "R": {"1": "G1", "2": "G2", "3": "G3"},
            "S": {"1": "L1", "5": "L5"},
        } 
        
        if system not in freq_num_to_freq_name.keys():
            raise ValueError(f"GNSS {system!r} is not defined. Following GNSS identifiers are available: "
                      "{''.join(list(freq_num_to_freq_name.keys()))}")
            return None
        
        if freq_num not in freq_num_to_freq_name[system].keys():
            raise ValueError(f"GNSS frequency band number {system}:{freq_num} is not defined. Following frequency band "
                      f"numbers are available for GNSS {system!r}: "
                      f"{''.join(list(freq_num_to_freq_name[system].keys()))}")
            return None
        
        return freq_num_to_freq_name[system][freq_num]
    
    
    @staticmethod
    def _gnss_to_antex_freq(system: str, frequency: str) -> Union[None, str]:
        """Get ANTEX frequency based on given GNSS and frequency
 
        Args: 
            system:     GNSS identifier (e.g. E=Galileo, G=GPS, ...)
            frequency:  GNSS frequency related to given 'system' argument (e.g. E1, E5a, L1)
            
        Returns:
            ANTEX frequency identifier or None if no ANTEX frequency identifier are defined for given
            system:frequency combination
        """
        
        # GNSS          GNSS freq        ANTEX freq
        # ___________________________________________
        # C (BeiDou):   B1               'C02'
        #               B2               'C07'
        #               B3               'C06'
        # G (GPS):      L1               'G01'
        #               L2               'G02'
        #               L5               'G05'
        # R (GLONASS):  G1               'R01'
        #               G2               'R02'
        # E (Galileo):  E1               'E01'
        #               E5 (E5a+E5b)     'E08'
        #               E5a              'E05'
        #               E5b              'E07'
        #               E6               'E06'
        # I (IRNSS):    L5               'I05'
        #               S                'I09'
        # J (QZSS):     L1               'J01'
        #               L2               'J02'
        #               L5               'J05'
        #               LEX              'J06'
        # S (SBAS):     L1               'S01'
        #               L5               'S05'
        gnss_to_antex_freq = {
            "C": {"B1": "C02", "B2": "C07", "B3": "C06"},
            "E": {"E1": "E01", "E5": "E08", "E5a": "E05", "E5b": "E07", "E6": "E06"},
            "G": {"L1": "G01", "L2": "G02", "L5": "G05"},
            "I": {"L5": "I05", "S": "I09"},
            "J": {"L1": "J01", "L2": "J02", "L5": "J05", "LEX": "J06"},
            "R": {"G1": "R01", "G2": "R02", "G3": "R03"},
            "S": {"L1": "S01", "L5": "S05"},
        }
        
        if system not in gnss_to_antex_freq.keys():
            raise ValueError(f"GNSS {system!r} is not defined. Following GNSS identifiers are available: "
                      "{''.join(list(gnss_to_antex_freq.keys()))}")
            return None
        
        if frequency not in gnss_to_antex_freq[system].keys():
            raise ValueError(f"GNSS frequency {system}:{frequency} is not defined. Following frequencies are available for GNSS {system!r}: "
                      "{''.join(list(gnss_to_antex_freq[system].keys()))}")
            return None
        
        return gnss_to_antex_freq[system][frequency]
    
    
    def _used_date(
            self, 
            given_date: Union[datetime.datetime, datetime.date],
            satellite: str, 
    ) -> Union[datetime.datetime, None]:
        """Choose correct date for use of satellite antenna corrections

        Satellite antenna correction are time dependent.

        Args:
            given_date (datetime.date):   Given date used for finding corresponding time period in ANTEX file
            satellite (str):              Satellite identifier.

        Returns:
            Date for getting correct satellite antenna corrections related to given date
        """
        used_date = None
        given_date = datetime.datetime.combine(given_date, datetime.time())  # conversion from date to datetime

        for date in sorted(self.data[satellite]):
            if date <= given_date:
                used_date = date

        if (used_date is None) or (given_date > self.data[satellite][used_date]["valid_until"]):
            warn(f"No satellite phase center offset is given for satellite {satellite} and date {given_date}.")

        return used_date
