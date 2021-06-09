"""A parser for reading troposphere results in SNX format

Description:
------------

The implementation is based on example output files from Bernese. The SINEX_TRO format is an extension of the regular
SINEX format, but mostly uses custom blocks. The following blocks are found in the example file:
+FILE/REFERENCE           (defined in SINEX 2.02)                                                      
+TROP/DESCRIPTION         (custom block)
+TROP/STA_COORDINATES     (custom block)
+TROP/SOLUTION            (custom block)

The format of the custom blocks are derived by reading example files and blocks defined in the format that is not 
present in the example files are not implemented yet.

Format description: https://files.igs.org/pub/data/format/sinex_tropo.txt

"""

# Standard library imports
from datetime import datetime

# External library imports
import numpy as np

# Midgard imports
from midgard.dev import plugins
from midgard.parsers._parser_sinex import SinexParser, SinexBlock, SinexField, parsing_factory


@plugins.register
class BernTropSnxParser(SinexParser):
    """A parser for reading data from Bernese troposphere files in SNX format
    """

    def __init__(self, file_path, encoding=None):
        """Set up the basic information needed by the parser

        Args:
            file_path (String/Path):    Path to file that will be read.
            encoding (String):          Encoding of file that will be read.
        """
        super().__init__(file_path, encoding)

    def setup_parser(self):
        return {self.file_reference, self.trop_description, self.trop_sta_coordinates, self.trop_solution}

    @property
    def trop_description(self):
        """Custom made block describing the solution.
        
        Is a list of keywords and values

        Example:
            +TROP/DESCRIPTION
            *_________KEYWORD_____________ __VALUE(S)_______________________________________
             ELEVATION CUTOFF ANGLE                             3
             SAMPLING INTERVAL                                180
             SAMPLING TROP                                   7200
             TROP MAPPING FUNCTION         WET VMF
             SOLUTION_FIELDS_1             TROTOT STDDEV TGNTOT STDDEV TGETOT STDDEV
            -TROP/DESCRIPTION
            
                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789


        """
        return SinexBlock(
            marker="TROP/DESCRIPTION",
            fields=(
                SinexField("keyword", 1, "U29"),
                SinexField("value", 31, "U49"),

            ),
            parser=self.parse_trop_description,
        )

    def parse_trop_description(self, data):
        """Parser for TROP/DESCRIPTION data

        Data not in use yet:
            Simply store each keyword, value pair in self.data as strings.
         
        Args:
            data (numpy.array):  Input data, raw data for TROP/DESCRIPTION block.
        """
        self.data.update(zip(data["keyword"], data["value"]))
            
    @property
    def trop_sta_coordinates(self):
        """Custom made block with station coordinates
        
        Example:
            *SITE PT SOLN T __STA_X_____ __STA_Y_____ __STA_Z_____ SYSTEM REMRK
             AASC  A    1 P  3172870.246   604208.664  5481574.631 IGS14  NMA
             ADAC  A    1 P  1916240.238   963577.117  5986596.696 IGS14  NMA

                      1111111111222222222233333333334444444444555555555566666666667777777777
            01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="TROP/STA_COORDINATES",
            fields=(
                SinexField("site_name", 1, "U4"),
                SinexField("point_code", 6, "U2"),
                SinexField("soln", 9, "U4"),
                SinexField("obs_code", 14, "U1"),
                SinexField("sta_x", 16, "f8"),
                SinexField("sta_y", 29, "f8"),
                SinexField("sta_z", 41, "f8"),
                SinexField("system", 55, "U6"),
                SinexField("remark", 62, "U17"),
            ),
            parser=self.parse_trop_sta_coordinates,
        )

    # Data not in use yet: Use a simple default parser converting each sinex field into a column of data
    parse_trop_sta_coordinates = parsing_factory()
    
    @property
    def trop_solution(self):
        """Custom block containing troposphere estimates.
        
        Unit is assumed to be millimeter.
        
        Example:
        *SITE ____EPOCH___ TROTOT STDDEV  TGNTOT STDDEV  TGETOT STDDEV
         AASC 20:001:00000 2388.6    1.4  -0.813  0.087  -0.232  0.088
         AASC 20:001:07200 2337.3    0.9  -0.784  0.078  -0.197  0.078

                  1111111111222222222233333333334444444444555555555566666666667777777777
        01234567890123456789012345678901234567890123456789012345678901234567890123456789
        """
        return SinexBlock(
            marker="TROP/SOLUTION",
            fields=(
                SinexField("site_name", 1, "U4"),
                SinexField("epoch", 6, "O", "epoch"),
                SinexField("trop_tot", 19, "f8"),
                SinexField("trop_tot_std", 26, "f8"),
                SinexField("trop_gn_tot", 34, "f8"),
                SinexField("trop_gn_tot_std", 41, "f8"),
                SinexField("trop_ge_tot", 49, "f8"),
                SinexField("trop_ge_tot_std", 56, "f8"),

            ),
            parser=self.parse_trop_solution,
        )
    
    def parse_trop_solution(self, data):
        """Parsers for TROP/SOLUTION data
        """
        for line in data:
            line_dict = dict(zip(data.dtype.names, line))
            sta = line_dict.pop("site_name")
            self.data.setdefault(sta, {}).update(line_dict)
            