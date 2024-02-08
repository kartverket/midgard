"""Write a-priori Bernese station velocity file in *.VEL format

Description:
------------

"""
# Standard library imports
from datetime import datetime
from pathlib import PosixPath
from typing import Any, Dict

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

@plugins.register
def bernese_vel(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
        datum: str = "UNKNOWN",
        agency: str = "UNKNOWN",
        write_nan_site_vel: bool = False,
) -> None:
    """Write a-priori Bernese station velocity file in *.VEL format

    Args:
        file_path:             File path of Bernese *.VEL output file
        site_info:             Dictionary with station information, whereby station name is the key and a dictionary
                               with site information the value.
        datum:                 Reference system name of site coordinates (e.g. IGb14)
        agency:                Abbreviation of agency producing the file (e.g. IGS)
        write_nan_site_vel:    Write site velocities, which has Not a Number (NaN) as value.
    """


    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # NMA OPERAX solution 20221025                                     25-OCT-22 11:22
    # --------------------------------------------------------------------------------
    # LOCAL GEODETIC DATUM: IGb14           
    #
    # NUM  STATION NAME           VX (M/Y)       VY (M/Y)       VZ (M/Y)  FLAG   PLATE
    #
    #   1  ADAC 10337M001         -0.01860        0.00940        0.00810    A    1+NK
    #   2  ALES 10336M001         -0.01480        0.01180        0.01000    A    1+NK
    #   3  ANDO 10333M001         -0.01730        0.00940        0.00840    A    1+NK
    #   4  ARGI 10117M002         -0.01360        0.01310        0.00780    Ib08 EURA
    #   5  BJOC 10339M001         -0.01430        0.01190        0.01140    A    1+NK
    #   6  BMLC 10340M001         -0.01410        0.01310        0.00990    A    1+NK
    #   7  BOD3 10326M002         -0.01620        0.01000        0.01080    A    1+NK
    #   8  BRGS 10310M001         -0.01410        0.01290        0.01020    A    1+NK
    #
    plate_def = {
        "african": "AFRC",
        "anatolian": "TODO", # what is the correct abbreviation for this plate?
        "antarctic": "ANTA",
        "antarctica": "ANTA",
        "arabian": "ARAB",
        "australian": "AUST",
        "cocos": "COCO",
        "eurasian": "EURA",
        "indian": "INDI",
        "Jjan de fuca plate": "JUFU",
        "nazca": "NAZC",
        "north america": "NOAM",
        "north american": "NOAM",
        "north-america": "NOAM",
        "pacific": "PCFC",
        "philippine": "PHIL",
        "south america": "SOAM",
    }
    
    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:
        
        # Write header
        fid.write(_get_header(datum, agency))

        # Write data
        for counter, station in enumerate(sorted(site_info.keys())):

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            #   1  ADAC 10337M001         -0.01860        0.00940        0.00810    A    1+NK
            crd = site_info[station]["site_coord"].get("last")
            if crd is None:
                log.warn(f"Station {station.upper()} ignored. Site velocity information are not given.")
                continue
            
            if not write_nan_site_vel:
                if np.isnan(crd.vel[0]):
                    continue
               
            idn = site_info[station]["identifier"]
  
            fid.write(
                "{number:>3}  {station:4} {domes:9} {x:16.5f} {y:14.5f} {z:14.5f} {flag:>4} {plate:>7}\n".format(
                    number=counter+1, 
                    station=station.upper(),
                    x=crd.vel[0],
                    y=crd.vel[1],
                    z=crd.vel[2],
                    domes= "" if idn.domes is None else idn.domes,
                    flag="A",
                    plate= "" if idn.tectonic_plate is None else plate_def[idn.tectonic_plate.lower()],
                    #TODO https://www.kaggle.com/code/karnikakapoor/earthquakes-and-tectonic-plates-seismic-analysis/notebook
                    #TODO https://gis.stackexchange.com/questions/88011/finding-country-from-coordinates-using-python
                    #TODO get tectonic plate for specific location python
                )
            )
  
            
def _get_header(datum: str, agency: str) -> str:
    """Get header
    
    Args:
        datum:    Reference system name of site coordinates (e.g. IGb14)
        agency:   Abbreviation of agency producing the file
        
    Return:
        Header as string
    """
    solution = f"{agency.upper()} solution {datetime.now().strftime('%Y%m%d')}"
    return (f"{solution:64s} {datetime.now().strftime('%d-%b-%y %H:%M').upper()}\n"
              f"{'-'*80}\n"
              f"LOCAL GEODETIC DATUM: {datum:17s} \n\n"
              f"NUM  STATION NAME           VX (M/Y)       VY (M/Y)       VZ (M/Y)  FLAG   PLATE\n\n"        
    )  