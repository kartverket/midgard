"""Write a-priori Bernese station coordinate file in *.CRD format

Description:
------------

"""
# Standard library imports
from datetime import datetime
from pathlib import PosixPath
from typing import Any, Dict, Union

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

@plugins.register
def bernese_crd(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
        datum: str = "UNKNOWN",
        epoch: Union[datetime, None] = None,
        agency: str = "UNKNOWN",
        write_nan_site_coord: bool = False,
) -> None:
    """Write a-priori Bernese station coordinate file in *.CRD format

    Args:
        file_path:             File path of Bernese *.CRD output file
        site_info:             Dictionary with station information, whereby station name is the key and a dictionary
                               with site information the value.
        datum:                 Reference system name of site coordinates (e.g. IGb14)
        epoch:                 Reference epoch of site coordinates in format yyyy-mm-dd HH:MM:SS (e.g. 
                               2015-01-01 00:00:00)
        agency:                Abbreviation of agency producing the file (e.g. IGS)
        write_nan_site_coord:  Write site coordinates, which has Not a Number (NaN) as value.
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # Midgard solution 
    # Igb14 final solution 20200424                                    24-APR-20 11:22
    # --------------------------------------------------------------------------------
    # LOCAL GEODETIC DATUM: IGb14             EPOCH: 2010-01-01 00:00:00
    #
    # NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG
    #
    #   1  ADAC 10337M001    1916240.41921   963577.02201  5986596.60366    A
    #   2  ALES 10336M001    2938027.25081   319096.42857  5633414.01485    A
    #   3  ANDO 10333M001    2175765.79500   624248.25920  5943417.81838    A
    #   4  ARGI 10117M002    2981489.76001  -354651.57251  5608475.00699    A
    #   5  BJOC 10339M001    2946468.00741   424528.51455  5622600.18054    A
    #   6  BMLC 10340M001    3203434.97421   291656.28808  5489224.18062    A
    #   7  BOD3 10326M002    2391774.15719   615615.08218  5860966.03006    A
    #   8  BRGS 10310M001    3155871.06890   290902.95229  5516573.62094    A
    #
    
    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:
        
        # Write header
        fid.write(_get_header(datum, epoch, agency))

        # Write data
        for counter, station in enumerate(sorted(site_info.keys())):

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            #   1  ADAC 10337M001    1916240.41921   963577.02201  5986596.60366    A
            crd = site_info[station]["site_coord"].get("last")
            if crd is None:
                log.warn(f"Station {station.upper()} ignored. Site coordinate information are not given.")
                continue
            
            if not write_nan_site_coord:
                if np.isnan(crd.pos.trs.x):
                    continue
               
            idn = site_info[station]["identifier"]
  
            fid.write(
                "{number:>3}  {station:4} {domes:9} {x:16.5f} {y:14.5f} {z:14.5f} {flag:>4}\n".format(
                    number=counter+1, 
                    station=station.upper(),
                    x=crd.pos.trs.x,
                    y=crd.pos.trs.y,
                    z=crd.pos.trs.z,
                    domes= "" if idn.domes is None else idn.domes,
                    flag="A",
                )
            )
  
            
def _get_header(datum: str, epoch: Union[datetime, None], agency: str) -> str:
    """Get header
    
    Args:
        datum:    Reference system name of site coordinates (e.g. IGb14)
        epoch:    Reference epoch of site coordinates 
        agency:   Abbreviation of agency producing the file
        
    Return:
        Header as string
    """    
    epoch = epoch.strftime("%Y-%m-%d %H:%M:%S") if epoch else "UNKNOWN"
    solution = f"{agency.upper()} solution {datetime.now().strftime('%Y%m%d')}"
    return (f"{solution:64s} {datetime.now().strftime('%d-%b-%y %H:%M').upper()}\n"
              f"{'-'*80}\n"
              f"LOCAL GEODETIC DATUM: {datum:17s} EPOCH: {epoch}\n\n"
              f"NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG\n\n"        
    )      
