"""Write site information file for GAMIT

Description:
------------


"""

# Standard library imports
from datetime import datetime
from pathlib import PosixPath
import re
from typing import Any, Dict

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

# Translation between IGS antenna reference point and GAMIT height code
REFERENCE_POINT = {"BAM": "DHARP",
                   "BCR": "DHBCR",
                   "BDG": "",
                   "BGP": "DHBGP",
                   "BPA": "DHBPA",
                   "TCR": "DHTCR", #??
                   "TDG": "",
                   "TGP": "DHTGP",
                   "TOP": "DHARP",
                   "TPA": "",
}

@plugins.register
def gamit_station_info(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
) -> None:
    """Write site information file for GAMIT

    Args:
        file_path:       File path of site information GAMIT output file
        site_info:       Dictionary with station information, whereby station name is the key and a dictionary with 
                         site information the value.
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # *          Gamit station.info
    # *
    # *SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN          
    #  0001  GEONET0001        2011 060 00 00 00  9999 999 00 00 00   0.0000  DHBGP   0.0000   0.0000  TRIMBLE NETR9         Nav 4.17 Sig 0.00      4.17  --------------------  TRM29659.00      GSI    --------------------
    #  0002  GEONET0002        2011 060 00 00 00  9999 999 00 00 00   0.0000  DHBGP   0.0000   0.0000  TRIMBLE NETR9         Nav 4.17 Sig 0.00      4.17  --------------------  TRM29659.00      GSI    --------------------

    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:
        
        # Write header
        fid.write("*          Gamit station.info\n")
        fid.write("*          Generated by Midgard, {datetime.now():%Y-%m-%d %H:%M}\n")
        fid.write("*SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN\n")

        for station, values in site_info.items():
            name = "----------------"
            start = datetime.max
            stop = datetime.min
            last_antenna = False
            last_receiver = False
            a_iter = iter(values["antenna"])
            r_iter = iter(values["receiver"])
            
            try:
                a = next(a_iter)
            except StopIteration:
                last_antenna = True
                
            try:
                r = next(r_iter)
            except StopIteration:
                last_receiver = True
                
            if "reference_point" not in dir(a):
                log.warn(f"Skip station {station.upper()}. Antenna reference point information is not given in source '{a.source}'.")
                continue
            
            while(not last_antenna and not last_receiver):
                # Reciever information
                r_type = r.type
                r_serial_number = r.serial_number

                # Firmware information
                prog = re.compile("\d*\.?\d+(?:\d+)?") 
                if prog.fullmatch(r.firmware):
                    r_firmware = r.firmware
                    r_version = "--------------------"
                elif matches:=prog.findall(r.firmware):
                    r_firmware = matches[0]
                    r_version = r.firmware
                else:
                    r_version = "--------------------"
                    r_firmware = "-----"

                # Antenna information
                a_type = a.type
                radome = a.radome_type if a.radome_type else "-----"
                a_serial_number = a.serial_number
                start = max(a.date_from, r.date_from)
                stop = min(a.date_to, r.date_to)

                # Eccentricity information
                height_code = REFERENCE_POINT.get(a.reference_point, "-----")
                e_start = values["eccentricity"].get(start)
                e_end = values["eccentricity"].get(stop)

                if e_end and e_start and (e_start.dpos != e_end.dpos):
                    log.warn(f"Eccentricity for {station} changed between {start:%Y-%m-%d} and {stop:%Y-%m-%d} ({e_start.dpos} vs {e_end.dpos})")

                if e_start:
                    height = e_start.up
                    east = e_start.east
                    north = e_start.north
                else:
                    if e_end:
                        height = e_end.up
                        east = e_end.east
                        north = e_end.north
                        log.warn(f"No ecc info for {station} at {start:%Y-%m-%d}, but found some for {stop:%Y-%m-%d} ({e_end.dpos})")
                    else:
                        height = 0
                        east = 0
                        north = 0

                fid.write(f" {station.upper()}  {name:16}  {start:%Y %j %H %M %S}  {stop:%Y %j %H %M %S}  {height:7.4f}  {height_code:5}  {north:7.4f}  {east:7.4f}  {r_type:20}  {r_version:20}  {r_firmware:>5}  {r_serial_number:20}  {a_type:15}  {radome:5}  {a_serial_number:20}\n")

                if a.date_to <= stop:
                    try:
                        a = next(a_iter)
                    except StopIteration:
                        last_antenna = True

                if r.date_to <= stop:
                    try:
                        r = next(r_iter)
                    except StopIteration:
                        last_receiver = True
                    
        
