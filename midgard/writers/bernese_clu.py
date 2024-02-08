"""Write a-priori Bernese station cluster file in *.CLU format

Description:
------------

"""
# Standard library imports
from datetime import datetime
from pathlib import PosixPath
from typing import Any, Dict

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

@plugins.register
def bernese_clu(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
        agency: str = "UNKNOWN",
) -> None:
    """Write a-priori Bernese station cluster file in *.CLU format

    Args:
        file_path:             File path of Bernese *.CLU output file
        site_info:             Dictionary with station information, whereby station name is the key and a dictionary
                               with site information the value.
        agency:                Abbreviation of agency producing the file (e.g. IGS)
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # BSW 5.2: PGS PUNKTLISTE                                          02-JUN-20 10:03
    # --------------------------------------------------------------------------------
    #
    # STATION NAME      CLU
    # ****************  ***
    # 0ABI                1
    # AASC                1
    # ADAC                1 
    # AKRC                1
    # ALES                1
    #
    
    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:
        
        # Write header
        fid.write(_get_header(agency))

        # Write data
        for counter, station in enumerate(sorted(site_info.keys())):

            # ----+----1----+----2----+----3----+----4----+----5
            # 0ABI                1             
            fid.write(
                "{station:4} {cluster:16}\n".format(
                    station=station.upper(),
                    cluster=1,
                )
            )
 
    
def _get_header(agency: str) -> str:
    """Get header
    
    Args:
        agency:   Abbreviation of agency producing the file
        
    Return:
        Header as string
    """
    solution = f"{agency.upper()} solution"
    return (f"{solution:64s} {datetime.now().strftime('%d-%b-%y %H:%M').upper()}\n"
              f"{'-'*80}\n\n"
              f"STATION NAME      CLU\n"        
              f"****************  ***\n"
    )   
                 
