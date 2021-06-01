"""A parser for reading troposphere files in Bernese TRP format


Example:
--------

    from analyx import parsers
    p = parsers.parse_file(parser_name='bernese_trp', file_path='F1_210300.TRP')
    data = p.as_dict()

Description:
------------

Reads data from files troposphere files in TRP format

"""
# Standard library imports
from datetime import datetime
from typing import Any, Callable, Dict, List

# Midgard imports
from midgard.data import dataset
from midgard.dev import plugins
from midgard.files import files
from midgard.parsers import LineParser


@plugins.register
class BerneseTrpPaser(LineParser):
    """A parser for reading troposphere files in Bernese TRP format


    Following **data** can be available after reading troposphere files in Bernese TRP file:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | TODO                 |                                                                                      |

    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | TODO                 |                                                                                      |
    | \__data_path__       | File path                                                                            |
    | \__params__          | np.genfromtxt parameters                                                             |
    | \__parser_name__     | Parser name                                                                          |
    """
    

        
    def setup_parser(self) -> Dict[str, Any]:
        """Set up information needed for the parser

        This should return a dictionary with all parameters needed by np.genfromtxt to do the actual parsing.

        Returns:
            Dict:  Parameters needed by np.genfromtxt to parse the input file.
        """

        # Parse header
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+
        # RNX2SNX_210300: Final coordinate/troposphere results             08-FEB-21 22:27
        # -------------------------------------------------------------------------------------------------------------------------------------
        #  A PRIORI MODEL:  -17   MAPPING FUNCTION:    8   GRADIENT MODEL:    4   MIN. ELEVATION:    5   TABULAR INTERVAL:  7200 / 86400
        #
        #  STATION NAME     FLG   YYYY MM DD HH MM SS   YYYY MM DD HH MM SS   MOD_U   CORR_U  SIGMA_U TOTAL_U  CORR_N  SIGMA_N  CORR_E  SIGMA_E
        self._parse_header()
        
        # Parse data
        #
        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----
        #  0ABI              A    2021 01 30 00 00 00                         2.1568  0.01970 0.00116 2.17652 -0.00005 0.00007  0.00015 0.00008
        #  0ABI              A    2021 01 30 02 00 00                         2.1562  0.01810 0.00082 2.17426 -0.00007 0.00007  0.00017 0.00007
        #  0ABI              A    2021 01 30 04 00 00                         2.1555  0.01948 0.00079 2.17499 -0.00010 0.00006  0.00019 0.00006
        #  AASC              A    2021 01 30 00 00 00                         2.2481  0.04025 0.00122 2.28832 -0.00009 0.00007 -0.00054 0.00008  
        return dict(
            skip_header=6,
            names=(
                "station", 
                "flag", 
                "from_time", 
                "to_time", 
                "zhd", 
                "zwd", 
                "sigma_zwd", 
                "ztd", 
                "gradient_ns", 
                "sigma_gradient_ns", 
                "gradient_ew", 
                "sigma_gradient_ew",
            ),
            delimiter=(19, 1, 23, 23, 9, 9, 8, 8, 9, 8, 9, 8),
            dtype=("U19", "U1", "U23", "U23", "f8", "f8", "f8", "f8", "f8", "f8", "f8", "f8"),
            autostrip=True,
        )


    def _parse_header(self) -> None:
        """Parse header
        """
        idx_def = {
                3: "apriori_troposphere_model", 
                6: "mapping_function",
                9: "gradient_model",
                12: "elevation_cutoff",
                #15: "tabular_intervall",     
        }
        
        apriori_troposphere_model_def = {
                "-1": "Saastamoinen",
                "-2": "Hopfield (Remondi)",
                "-3": "Essen and Froome",
                "-4": "Marini-Murray (SLR)",
                "-5": "Saastamoinen with Niell dry mapping",
                "-6": "GPT with GMF dry+wet mapping",
                "-7": "ECMWF with VMF1 dry+wet mapping",
                "-8": "Mendes-Pavlis (SLR)",
               "-11": "Saastamoinen dry part only",
               "-12": "Hopfield dry part only",
               "-13": "Simplified Hopfield dry part only",
               "-15": "Saastamoinen dry with Niell dry mapping",
               "-16": "GPT dry with GMF dry mapping",
               "-17": "ECMWF dry with VMF1 dry mapping",
        }
        
        mapping_function_def = {
                 "1": "1/cos(z)",
                 "2": "Hopfield",
                 "3": "Dry Niell",
                 "4": "Wet Niell",
                 "5": "Dry GMF",
                 "6": "Wet GMT",
                 "7": "Dry VMF1",
                 "8": "Wet VMF1",
        }
        
        gradient_model_def = {
                 "0": "No estimation",
                 "1": "Tilting",
                 "2": "Linear",
                 "3": "TANZ from MacMillan (1995)",
                 "4": "CHENHER from Chen and Herring (1997)",           
        }
        
       
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            
            for line in fid: 

                if "A PRIORI MODEL" in line:
                    elements = line.split()

                    for idx, name in idx_def.items():
                        if name == "apriori_troposphere_model":
                            self.meta[name] = apriori_troposphere_model_def[elements[idx]]
                        elif name == "mapping_function":
                            self.meta[name] = mapping_function_def[elements[idx]]
                        elif name == "gradient_model":
                            self.meta[name] = gradient_model_def[elements[idx]]
                        else:
                            self.meta[name] = elements[idx]        
                    break
        return
    
    #
    # SETUP POSTPROCESSORS
    #
    def setup_postprocessors(self) -> List[Callable[[], None]]:
        """List steps necessary for postprocessing
        """
        return [
            self._time_to_datetime,
        ]

    def _time_to_datetime(self) -> None:
        """Convert time file entries to datetime objects
        """
        self.data["time"] = [datetime.strptime(v, "%Y %m %d %H %M %S") for v in self.data["from_time"]]
        del self.data["from_time"]
        
        # Normally no end period is given in TRP file
        if self.data["to_time"][0]:
            self.data["to_time"] = [datetime.strptime(v, "%Y %m %d %H %M %S") for v in self.data["to_time"]]
                

    #
    # GET DATASET
    #
    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        Returns:
            Midgard Dataset where troposphere observation are stored with following fields:

       |  Field                   | Type           | Description                                                      |
       |--------------------------|----------------|------------------------------------------------------------------|
       | flag                     | numpy.ndarray  | Station flag (see section 24.7.1 of Bernese GNSS software        |
       |                          |                | version 5.2, November 2015)                                      |
       | gradients_ew             | numpy.ndarray  | Gradients in East/West in [m]                                    |
       | gradients_ns             | numpy.ndarray  | Gradients in North/South in [m]                                  |
       | sigma_gradients_ew       | numpy.ndarray  | Standard deviation of gradients in East/West in [m]              |
       | sigma_gradients_ns       | numpy.ndarray  | Standard deviation of gradients in North/South in [m]            |
       | sigma_zwd                | numpy.ndarray  | Standard devivation of ZWD in [m]                                |
       | station                  | numpy.ndarray  | Station name                                                     |
       | time                     | TimeTable      | Observation time given as TimeTable object                       |
       | zhd                      | numpy.ndarray  | Zenith Hydrostatic Delay (ZHD) from a-priori model in [m]        |
       | ztd                      | numpy.ndarray  | Zenith Total Delay (ZTD) in [m]                                  |
       | zwd                      | numpy.ndarray  | Zenith Wet Delay (ZWD) in [m]                                    |
        """
        
        skip_fields = ["to_time"]
        text_fields = ["flag", "station"]
        
        # Generate dataset
        dset = dataset.Dataset(num_obs=len(self.data["time"]))
        dset.meta = self.meta
        
        for field in self.data.keys():
            
            if field in skip_fields:
                continue
            
            if field in text_fields:
                
                if field == "station":
                    dset.add_text(field, val=[v.lower() for v in self.data[field]])
                else:
                    dset.add_text(field, val=self.data[field])
            
            elif field == "time":
                dset.add_time(field, val=self.data[field], scale="gps", fmt="datetime")
                
            else:
                dset.add_float(field, val=self.data[field], unit="meter")
                
        return dset
        
        
        
        
        
    
