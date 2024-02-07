"""Write Bernese abbreviation file in *.ABB format

Description:
------------

"""
# Standard library imports
from datetime import datetime
from pathlib import PosixPath
from string import ascii_lowercase
from typing import Any, Dict

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

_SECTION = "_".join(__name__.split(".")[-1:])

@plugins.register
def bernese_abb(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
        agency: str = "UNKNOWN",
) -> None:
    """Write Bernese abbreviation file in *.ABB format

    Args:
        file_path:             File path of Bernese *.ABB output file
        site_info:             Dictionary with station information, whereby station name is the key and a dictionary
                               with site information the value.
        agency:                Abbreviation of agency producing the file (e.g. IGS)
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # PPP_102070                                                       21-FEB-13 13:42
    # --------------------------------------------------------------------------------
    #
    # Station name             4-ID    2-ID    Remark                                 
    # ****************         ****     **     ***************************************
    # A001                     A001     A0     Added by SR updabb                     
    # A070                     A070     A7     Added by SR updabb                     
    # A091                     A091     91     Added by SR updabb  
                   
    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:
        
        # Write header
        # PPP_102070                                                       21-FEB-13 13:42
        # --------------------------------------------------------------------------------
        #
        # Station name             4-ID    2-ID    Remark                                 
        # ****************         ****     **     ***************************************
        fid.write(_get_header(agency))
        
        stations_2id = _get_2digit_station_list(site_info)
                
        for sta in sorted(site_info.keys()):
            
            # ----+----1----+----2----+----3----+----4----+----5----+----
            # A001                     A001     A0     Added by SR updabb                  
            fid.write(
                "{station:24} {station_4_id:8} {station_2_id:6} {remark}\n".format(
                    station=sta.upper(),
                    station_4_id=sta.upper(),
                    station_2_id=stations_2id[sta],
                    remark=f"Added by {agency.upper()}", 
                )
            )
        fid.write("\n")
                

#
# AUXILIARY FUNCTIONS
#
def _get_2digit_station_list(site_info: Dict[str, Any],) -> str:
    """Get 2-digit station list
    
    Args:
        site_info:  Dictionary with station information, whereby station name is the key and a dictionary with site 
                    information the value.
        
    Return:
        Dictionary with 4-digit station name as key and belonging 2-digit station name as value
    """

    stations_2id = dict()
    characters=ascii_lowercase+'0123456789'
    
    for sta in sorted(site_info.keys()):
        sta_2id = None
        if sta[0:2] not in stations_2id.values():
            sta_2id = sta[0:2]
        elif f"{sta[0]}{sta[2]}" not in stations_2id.values():
            sta_2id = f"{sta[0]}{sta[2]}"
        elif f"{sta[0]}{sta[3]}" not in stations_2id.values():
            sta_2id = f"{sta[0]}{sta[3]}"
        else:

            for ii in characters:
                if not f"{sta[0]}{ii}" in stations_2id.values():
                    sta_2id = f"{sta[0]}{ii}"
                    break
                
            for jj in characters:
                if not f"{jj}{sta[0]}" in stations_2id.values():
                    sta_2id = f"{jj}{sta[0]}"
                    break
                
            for kk in characters:
                for ll in characters:
                    if not f"{kk}{ll}" in stations_2id.values():
                        sta_2id = f"{kk}{ll}"
                        break


        if not sta_2id:
            log.fatal(f"No unique 2-digit station name found for station {sta.upper()}.")
            
        stations_2id.update({sta: sta_2id})

    return stations_2id  
      
                   
def _get_header(agency: str) -> str:
    """Get header
    
    Args:
        agency:   Abbreviation of agency producing the file
    """ 
    solution = f"{agency.upper()} solution"
    return (f"{solution:64s} {datetime.now().strftime('%d-%b-%y %H:%M').upper()}\n"
            f"{'-'*80}\n\n"
            "Station name             4-ID    2-ID    Remark \n"
            "****************         ****     **     ***************************************\n"        
    )      


