"""A parser for reading GipsyX summary output file

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='gipsyx_summary', file_path='gipsyx_summary')
    data = p.as_dict()

Description:
------------

Reads data from files in GipsyX summary output format.

"""
# Standard library imports
from typing import Any, Callable, Dict, List

# Midgard imports
from midgard.data import dataset
from midgard.dev import log
from midgard.dev import plugins
from midgard.files import files
from midgard.parsers import LineParser, Parser


@plugins.register
class GipsyxSummary(Parser):
    """A parser for reading GipsyX summary file

    GipsyX summary file **data** are grouped as follows:

    | Key                   | Description                                                                          |
    |-----------------------|--------------------------------------------------------------------------------------|
    | position              | Dictionary with position summary information                                         |
    | residual              | Dictionary with residual summary information                                         |
    | station               | Station name                                                                         |

    **position** entries are:

    | Key                   | Description                                                                          |
    |-----------------------|--------------------------------------------------------------------------------------|
    | pos_x                 | X-coordinate of station position solution                                            |
    | pos_y                 | Y-coordinate of station position solution                                            |
    | pos_z                 | Z-coordinate of station position solution                                            |
    | pos_vs_ref_x          | X-coordinate of difference between solution and reference of station coordinate      |
    | pos_vs_ref_y          | Y-coordinate of difference between solution and reference of station coordinate      |
    | pos_vs_ref_z          | Z-coordinate of difference between solution and reference of station coordinate      |
    | pos_vs_ref_e          | East-coordinate of difference between solution and reference of station coordinate   |
    | pos_vs_ref_n          | North-coordinate of difference between solution and reference of station coordinate  |
    | pos_vs_ref_v          | Vertical-coordinate of difference between solution and reference of station          |
    |                       | coordinate                                                                           |


    **residual** entries are:

    | Key                   | Description                                                                          |
    |-----------------------|--------------------------------------------------------------------------------------|
    | code_max              | Maximal residual of used pseudo-range observations                                   |
    | code_min              | Minimal residual of used pseudo-range observations                                   |
    | code_num              | Number of used pseudo-range observations                                             |
    | code_rms              | RMS of residuals from used pseudo-range observations                                 |
    | code_outlier_max      | Maximal residual of rejected pseudo-range observations                               |
    | code_outlier_min      | Minimal residual of rejected pseudo-range observations                               |
    | code_outlier_num      | Number of rejected pseudo-range observations                                         |
    | code_outlier_rms      | RMS of residuals from rejected pseudo-range observations                             |
    | phase_max             | Maximal residual of used phase observations                                          |
    | phase_min             | Minimal residual of used phase observations                                          |
    | phase_num             | Number of used phase observations                                                    |
    | phase_rms             | RMS of residuals from used phase observations                                        |
    | phase_outlier_max     | Maximal residual of rejected phase observations                                      |
    | phase_outlier_min     | Minimal residual of rejected phase observations                                      |
    | phase_outlier_num     | Number of rejected phase observations                                                |
    | phase_outlier_rms     | RMS of residuals from rejected phase observations                                    |


    and **meta**-data:

    | Key                  | Description                                                                          |
    |----------------------|--------------------------------------------------------------------------------------|
    | \__data_path__       | File path                                                                            |
    | \__parser_name__     | Parser name                                                                          |
    """

    def read_data(self) -> None:
        """Read data from the data file
        """

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8----+----+----9----+----0----+----1---
        # ---   Residual Summary:
        # ------------------------------------------------------------------
        # ---   included residuals  :      6082 (  98.4% )
        # ---   deleted residuals   :        96 (   1.6% )
        # ---      DataType           Status        RMS (m)         Max (m)         Min (m)         number (%)
        # ---   IonoFreeC_1P_2P   included      5.072441e-01    2.287646e+00   -1.699980e+00      3087 (  99.9% )
        # ---   IonoFreeC_1P_2P    deleted      2.334849e+01    3.292118e+01    2.549366e+00         2 (   0.1% )
        # ---
        # ---   IonoFreeL_1P_2P   included      7.227355e-03    2.717787e-02   -2.721378e-02      2995 (  97.0% )
        # ---   IonoFreeL_1P_2P    deleted      1.555886e+01    8.371774e+01   -7.268516e-02        94 (   3.0% )
        # ------------------------------------------------------------------
        #
        #                    PPP Solution: XYZ                                DeltaXYZ(Sol-Nom)               DeltaENV (meters)
        # TRO1 2102928.199489438 721619.5988837772 5958196.320616415 -1.819E-01  8.667E-02  1.660E-02  1.410E-01  1.407E-01  -3.445E-02

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8----+----+----9----+----0----+----1---
        # ---   Residual Summary:
        # ------------------------------------------------------------------
        # ---   No Residuals (or at least FilterResidualTracker has not been informed of any).
        # ------------------------------------------------------------------
        #
        #                    PPP Solution: XYZ                                DeltaXYZ(Sol-Nom)               DeltaENV (meters)
        # TRO1 2102928.381357 721619.512215 5958196.304021 0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00
        with files.open(self.file_path, mode="rt", encoding=self.file_encoding) as fid:
            self._parse_file(fid)

    def _parse_file(self, fid: "_io.TextIOWrapper") -> None:
        """Parse file
        
        Args:
            fid: File handle
        """
        names = [
            "station",
            "pos_x",
            "pos_y",
            "pos_z",
            "dpos_vs_ref_x",
            "dpos_vs_ref_y",
            "dpos_vs_ref_z",
            "dpos_vs_ref_e",
            "dpos_vs_ref_n",
            "dpos_vs_ref_v",
        ]
        for line in fid:

            # Skip lines
            if not line.strip() or ("PPP Solution" in line):
                continue

            # Parse residual header
            if line.startswith("---"):
                self._parse_header(line)
                continue

            # Parse position line
            words = line.split(maxsplit=10)
            self.data.setdefault("position", dict())
            for name, word in zip(names, words):
                if name == "station":
                    self.data["station"] = word
                    continue
                self.data["position"][name] = float(word)

    def _parse_header(self, line: str) -> None:
        """Parse header of file

        Args:
           line:  File line 
        """

        # Skip lines
        if line.startswith("----") or ("Residual Summary" in line):
            return

        self.data.setdefault("residual", dict())

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8--
        # ---   No Residuals (or at least FilterResidualTracker has not been informed of any).
        #
        # Set residual entries to NaN
        if "No Residuals" in line:
            entries = [
                "code_rms",
                "code_max",
                "code_min",
                "code_num",
                "code_outlier_rms",
                "code_outlier_max",
                "code_outlier_min",
                "code_outlier_num",
                "phase_rms",
                "phase_max",
                "phase_min",
                "phase_num",
                "phase_outlier_rms",
                "phase_outlier_max",
                "phase_outlier_min",
                "phase_outlier_num",
            ]
            for entry in entries:
                self.data["residual"][entry] = float("nan")

        # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----+----8----+----+----9----+
        # ---   included residuals  :      5225 (  99.9% )
        # ---   deleted residuals   :         3 (   0.1% )
        # ---      DataType           Status        RMS (m)         Max (m)         Min (m)         number (%)
        # ---   IonoFreeC_1P_2P   included      6.312075e-01    2.495345e+00   -2.457276e+00      2614 ( 100.0% )
        # ---   IonoFreeC_1P_2P    deleted      0.000000e+00    0.000000e+00    0.000000e+00         0 (   0.0% )
        # ---
        # ---   IonoFreeL_1P_2P   included      7.011136e-03    2.661300e-02   -2.358874e-02      2611 (  99.9% )
        # ---   IonoFreeL_1P_2P    deleted      3.601511e-02    3.983458e-02   -3.721420e-02         3 (   0.1% )
        #
        line = line.split()
        if len(line) == 10:

            if line[1] == "IonoFreeC_1P_2P":
                if line[2] == "included":
                    self.data["residual"].update(
                        {
                            "code_rms": float(line[3]),
                            "code_max": float(line[4]),
                            "code_min": float(line[5]),
                            "code_num": float(line[6]),
                        }
                    )
                if line[2] == "deleted":
                    self.data["residual"].update(
                        {
                            "code_outlier_rms": float(line[3]),
                            "code_outlier_max": float(line[4]),
                            "code_outlier_min": float(line[5]),
                            "code_outlier_num": float(line[6]),
                        }
                    )

            if line[1] == "IonoFreeL_1P_2P":
                if line[2] == "included":
                    self.data["residual"].update(
                        {
                            "phase_rms": float(line[3]),
                            "phase_max": float(line[4]),
                            "phase_min": float(line[5]),
                            "phase_num": float(line[6]),
                        }
                    )
                if line[2] == "deleted":
                    self.data["residual"].update(
                        {
                            "phase_outlier_rms": float(line[3]),
                            "phase_outlier_max": float(line[4]),
                            "phase_outlier_min": float(line[5]),
                            "phase_outlier_num": float(line[6]),
                        }
                    )

    def as_dataset(self) -> "Dataset":
        """Return the parsed data as a Dataset

        GipsyX summary results are added to Dataset 'meta' variable. 

        Args:
            dset: Dataset.

        Returns:
            A dataset containing the data.
        """
        dset = dataset.Dataset(num_obs=0)

        if not self.data:
            log.warn("No data in {self.file_path}.")
            return dset

        dset.meta["summary"] = self.data
        return dset
