"""A parser for reading Bernese CRD file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='bernese_crd', file_path='W20216.CRD')
    data = p.as_dict()

Description:
------------

Reads data from files in Bernese CRD format.

"""
# Standard library imports
from datetime import datetime
from typing import Any, Callable, Dict, List

# External library imports
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.data.time import Time
from midgard.files import files
from midgard.parsers import LineParser
from midgard.dev import plugins


@plugins.register
class BerneseCrdParser(LineParser):
    """A parser for reading Bernese CRD file

    Following **data** are available after reading Bernese CRD file:

    | Parameter           | Description                                                                           |
    | :------------------ | :------------------------------------------------------------------------------------ |
    | num                 | Number of station coordinate solution                                                 |
    | station             | 4-digit station identifier                                                            |
    | domes               | Domes number                                                                          |
    | gpssec              | Seconds of GPS week                                                                   |
    | pos_x               | X-coordinate of station position                                                      |
    | pos_y               | Y-coordinate of station position                                                      |
    | pos_z               | Z-coordinate of station position                                                      |
    | flag                | Flag                                                                                  |

    and **meta**-data:

    | Key                  | Description                                                                          |
    | :------------------- | :----------------------------------------------------------------------------------- |
    | \__data_path__       | File path                                                                            |
    | \__params__          | np.genfromtxt parameters                                                             |
    | \__parser_name__     | Parser name                                                                          |
    | ref_epoch            | Reference epoch of reference station coordinate in ISO format                        |
    |                      | yyyy-mm-ddTHH:MM:SS (e.g. 2025-01-01T00:00:00)                                       |
    | ref_frame            | Reference frame of reference station coordinate                                      |

    """

    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # Parse header 
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
        # 20216 Week solution coordinates and sinex                        23-OCT-18 07:05
        # --------------------------------------------------------------------------------
        # LOCAL GEODETIC DATUM: IGS14             EPOCH: 2018-10-03 12:00:00
        #
        # NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG
        #
        self._parse_header()

        # Parse data
        # 
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8--
        #   1  0ABI              2233557.47676   761080.39008  5906186.08412    A
        #   2  AASC              3172870.25685   604208.64396  5481574.60291    A
        #   3  ABMF 97103M001    2919785.71395 -5383745.04971  1774604.71351
        return dict(
            autostrip=True,
            comments="#",
            names=("num", "station", "domes", "pos_x", "pos_y", "pos_z", "flag"),
            delimiter=(3, 6, 10, 17, 15, 15, 5),
            dtype=("f8", "U4", "U10", "f8", "f8", "f8", "U1"),
            skip_header=6,
        )


    def _parse_header(self) -> None:
        """Parse header
        """
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: 
                
                if line.startswith("LOCAL GEODETIC DATUM"):
                    words = [w.strip() for w in line.replace("LOCAL GEODETIC DATUM:", "").replace("EPOCH:", "").split()]
        
                    self.meta["ref_frame"] = words[0]
                    self.meta["ref_epoch"] =  f"{words[1]}T{words[2]}"
                    break

    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [
            self._remove_blank_entries,
        ]

    def _remove_blank_entries(self) -> None:
        """Remove blank line entries, which are not automatically removed by np.genfromtxt
        """
        if "" in self.data["station"]:
            idx = "" == self.data["station"]  # get index of blank entries
            for key in self.data.keys():
                self.data[key] = self.data[key][~idx]  # Keep all entries, which are not blank

    #
    # GET DICTIONARY
    #
    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate dictionary with station identifier as keys

        Returns:
            Dictionary with station identifiers as keys.
        """
        dict_ = dict()

        for idx, sta in enumerate(self.data["station"]):
            dict_.update(
                {
                    sta.lower(): {
                        "num": self.data["num"][idx],
                        "domes": self.data["domes"][idx],
                        "pos_x": self.data["pos_x"][idx],
                        "pos_y": self.data["pos_y"][idx],
                        "pos_z": self.data["pos_z"][idx],
                        "flag": self.data["flag"][idx],
                    }
                }
            )

        return dict_


    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where station coordinates and belonging information are stored with following fields:

        |  Field                   | Type           | Description                                                      |
        | :----------------------- | :------------- | :--------------------------------------------------------------- |
        | domes                    | numpy.ndarray  | Domes number                                                     |
        | flag                     | numpy.ndarray  | Station flag (see section 24.7.1 of Bernese GNSS software        |
        |                          |                | version 5.2, November 2015)                                      |
        | station                  | numpy.ndarray  | Station name                                                     |
        | site_pos                 | PositionTable  | Station coordinates given as PositionTable object                |

            and following Dataset `meta` data:

        |  Entry              | Type  | Description                                                                    |
        | :------------------ | :---- | :----------------------------------------------------------------------------- |
        | \__data_path__      | str   | File path                                                                      |
        | ref_epoch           | str   | Reference epoch of reference station coordinate in ISO format                  |
        |                     |       | yyyy-mm-ddTHH:MM:SS (e.g. 2025-01-01T00:00:00)                                 |
        | ref_frame           | str   | Reference frame of reference station coordinate                                |
        """
             
        # Generate dataset
        dset = dataset.Dataset(num_obs=len(self.data["station"]))
        dset.meta = self.meta.copy()

        # Remove unnecessary entries in meta
        for key in ["__params__", "__parser_name__"]:
            del dset.meta[key]


        # Add fields to dataset        
        for field in ["domes", "flag", "station"]:
            
            if field == "station":
                dset.add_text(field, val=[v.lower() for v in self.data[field]])
            else:
                dset.add_text(field, val=self.data[field])

        dset.add_position(
            "site_pos", 
            time=Time(
                    [datetime.fromisoformat(dset.meta["ref_epoch"]) for ii in range(0, dset.num_obs)], 
                    scale="gps", 
                    fmt="datetime",
            ),
            system="trs", 
            val=np.stack((np.array(self.data["pos_x"]), np.array(self.data["pos_y"]), np.array(self.data["pos_z"])), axis=1),
        )
              
        return dset
