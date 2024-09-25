"""A parser for reading station information in Bernese STA format in Bernese v5.4 format


Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='bernese_sta_v52', file_path='NKG.STA')
    data = p.as_dict()

Description:
------------

Reads station information from files in STA format, whereby at the moment only the 'STATION INFORMATION' part is
parsed.

"""
# Standard library imports
from datetime import datetime
import itertools
import re
from typing import Any, Dict, Iterable, Tuple

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import ChainParser, ParserDef


@plugins.register
class BerneseStaParser(ChainParser):
    """A parser for reading station information in Bernese STA format in Bernese v5.4 format


    The parsed data are saved in variable **data** as a dictionay with 4-digit station name as key and a list with 
    station information dictionaries with following entries:

    | Key                          | Type     | Description                                                        |
    | :--------------------------- | :------- | :----------------------------------------------------------------- |
    | antenna_serial_number        | str      | Antenna serial number                                              |
    | antenna_serial_number_short  | str      | 6 last digits of antennna serial number                            |
    | antenna_type                 | str      | Antenna type                                                       |
    | date_from                    | datetime | Start date where station information is valid                      |
    | date_to                      | datetime | End date of station information                                    | 
    | domes                        | str      | Domes number                                                       |
    | description                  | str      | Description normally with station name and country code            |
    | eccentricity_east            | float    | East component of eccentricity in [m]                              |
    | eccentricity_north           | float    | North component of eccentricity in [m]                             |
    | eccentricity_up              | float    | Up component of eccentricity in [m]                                |
    | flag                         | str      | Flag number                                                        |
    | radome                       | str      | Antenna radome type                                                |
    | receiver_serial_number       | str      | Receiver serial number                                             |
    | receiver_serial_number_short | str      | 6 last digits of receiver serial number                            |
    | receiver_type                | str      | Receiver type                                                      |
    | remark                       | str      | Remark                                                             |

    and **meta**-data:

    | Key                  | Description                                                                        |
    |----------------------|------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                          |
    | \__parser_name__     | Parser name                                                                        |
    """


    def __init__(self, *args: Tuple[Any], **kwargs: Dict[Any, Any]):
        """
        Args:
            args:   Parameters without keyword.
            kargs:  Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.fields = list()  # Save field names, which are read. Needed by generating of dataset.

            
    def setup_parser(self) -> Iterable[ParserDef]:
        """Set up information needed for the parser

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """


        # Skip lines until 'TYPE 002: STATION INFORMATION' section
        skip_lines_parser = ParserDef(
            end_marker=lambda line, _ln, _n: (
                "TYPE 002: STATION INFORMATION" in line            # Start of station_information_parser
            ),
            label= lambda line, _ln: line,
            parser_def = {},
        )


        
        #
        # TYPE 002: STATION INFORMATION
        # -----------------------------
        #
        # STATION NAME          FLG          FROM                   TO         RECEIVER TYPE         RECEIVER SERIAL NBR   REC #   ANTENNA TYPE          ANTENNA SERIAL NBR    ANT #    NORTH      EAST      UP     AZIMUTH  LONG NAME  DESCRIPTION             REMARK
        # ****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ********************  ******  ********************  ********************  ******  ***.****  ***.****  ***.****  ****.*  *********  **********************  ************************
        # ALRT                  001  2002 07 16 00 00 00  2011 05 20 15 45 00  ASHTECH UZ-12         ZR520                    520  ASH701945D_M    NONE  CR520020903           999999    0.0000    0.0000    0.1000     0.0  ALRT00CAN  Alert (Ellesmere Islan  IGS.SNX
        # ALRT                  001  2011 05 20 15 51 00  2099 12 31 00 00 00  ASHTECH UZ-12         UC220                    220  ASH701945D_M    NONE  CR520020903           999999    0.0000    0.0000    0.1000     0.0  ALRT00CAN  Alert (Ellesmere Islan  IGS.SNX
        # ARTU                  001  1999 08 05 00 00 00  2018 09 06 05 00 00  ASHTECH Z-XII3                              999999  ASH700936D_M    DOME  CR13077               999999    0.0000    0.0000    0.0796     0.0  ARTU00RUS  Arti, Russian Federati  IGS.SNX      
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7
        station_information_parser = ParserDef(
            end_marker=lambda _l, _ln, next_line: next_line.strip().startswith("TYPE 003: HANDLING OF STATION PROBLEMS"),
            label=lambda line, _ln: bool(re.match(r"\w\w\w\w ", line)),
            parser_def={
                True: {   
                    "parser": self._station_information,
                    "fields": {
                        "station":   (0, 4),
                        "domes": (5, 14),
                        "flag": (15, 25),
                        "date_from": (26, 46),
                        "date_to": (47, 67),
                        "receiver_type": (68, 89),
                        "receiver_serial_number": (90, 111),
                        "receiver_serial_number_short": (112, 119),
                        "antenna_type": (120, 136),
                        "radome_type": (137, 141),
                        "antenna_serial_number": (142, 163),
                        "antenna_serial_number_short": (164, 171),
                        "eccentricity_north": (172, 181),
                        "eccentricity_east": (182, 191),
                        "eccentricity_up": (192, 201),
                        "azimuth": (202, 209),
                        "long_name": (210, 220),
                        "description": (221, 244),
                        "remark": (245, None),
                    },
                },
            },
        )
     
        return itertools.chain([
            skip_lines_parser, 
            station_information_parser, 
        ])
  

    #
    # PARSERS
    #
    def _station_information(self, line: Dict[str, str], cache: Dict[str, Any]) -> None:
        """Parse station information part of file
        """
        station = line["station"].lower()
        self.data.setdefault(station, list())
        
        # Define date period
        line["date_from"] = _date2datetime(line["date_from"])
        line["date_to"] = _date2datetime(line["date_to"])
        
        # Add rest of entries to dictionary
        del line["station"]
        for entry in ["eccentricity_north", "eccentricity_east", "eccentricity_up"]:
            line[entry] = float(line[entry])
        self.data[station].append(line)


#
# AUXILIARY FUNCTIONS
#
def _date2datetime(date: str) -> datetime:
    """Convert date to datetime object
    
    Args:
        date: Date in format year month day hour minute second (e.g. 2008 09 25 00 00 00)
   
    Returns:
        Date as datetime object
    """
    year, month, day, hour, minute, second = date.split()
    return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
