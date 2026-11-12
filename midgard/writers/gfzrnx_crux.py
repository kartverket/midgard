"""Write 'crux' site information file for gfzrnx

Description:
------------


"""

# Standard library imports
from datetime import datetime, timedelta
from pathlib import PosixPath
from typing import Any, Dict

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

@plugins.register
def gfzrnx_crux(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
) -> None:
    """Write 'crux' site information file for gfzrnx

    Args:
        file_path:       File path of gfzrnx 'crux' site information file output file. File path can include {station}
                         or {STATION} placeholders, which should be replaced with 4-digit or 9-digit station name
                         either in lowercase (e.g. ales/ales00nor) or uppercase (e.g. ALES/ALES00NOR).
        site_info:       Dictionary with station information, whereby station name is the key and a dictionary with 
                         site information the value.
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # update_insert:
    # O - ALES00NOR
    # \"MARKER NAME\"         : { 0: \"ALES00NOR\" }
    # \"MARKER NUMBER\"       : { 0: \"10336M001\" }
    # \"OBSERVER / AGENCY\"   : { 0: \"Norwegian Mapping Authority\" }
    # \"REC # / TYPE / VERS\" + 19970127:00000  20000426:00000  : { 0: \"3511A10131\", 1: \"TRIMBLE 4000SSI\", 2: \"7.28\" }
    # \"REC # / TYPE / VERS\" + 20000426:00000  20090908:36000  : { 0: \"220191079\", 1: \"TRIMBLE MS750\", 2: \"1.20\" }
    # \"ANT # / TYPE\" + 19970127:00000  19980613:00000  : { 0: \"220098660\", 1: \"TRM29659.00\", 2: \"FAIL\" }
    # \"ANT # / TYPE\" + 19980613:00000  20080624:00000  : { 0: \"220098660\", 1: \"TRM29659.00\", 2: \"SCIS\" }
    # \"ANT # / TYPE\" + 20080624:00000  99991231:86399  : { 0: \"30767859\", 1: \"TRM55971.00\", 2: \"NONE\" }
    # \"APPROX POSITION XYZ\" +  19970127:00000  99991231:86399  : { 0: \"2938027.6157\", 1: \"319096.2115\", 2: \"5633413.7914\" }
    # \"ANTENNA: DELTA H/E/N\" + 19970127:00000  99991231:86399  : { 0: \"5.536\", 1: \"0.005\", 2: \"-0.001\" }
    # \"ANTENNA: DELTA H/E/N\" + 19970127:00000  99991231:86399  : { 0: \"5.536\", 1: \"0.005\", 2: \"-0.001\" }


    log.info(f"Write station-dependent files {file_path}")

    for station in sorted(site_info.keys()):

        # Replace {station} and {STATION} placeholder
        file_path_replaced = str(file_path).replace("{station}", station.lower()).replace("{STATION}", station.upper())

        with files.open(file_path_replaced, create_dirs=True, mode="wt") as fid:

            log.debug(f"Write file {file_path_replaced}")

            fid.write("update_insert:\n")

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # O - ALES00NOR
            # \"MARKER NAME\"         : { 0: \"ALES00NOR\" }
            # \"MARKER NUMBER\"       : { 0: \"10336M001\" }
            # \"OBSERVER / AGENCY\"   : { 0: \"Norwegian Mapping Authority\", 1: \"Norwegian Mapping Authority\" }
            idn = site_info[station]["identifier"]

            # Write 9-digit station name
            if "country_code" in dir(idn): 
                fid.write(
                    "O - {station:4}00{country_code:3}:\n".format(
                        station=station.upper(),
                        country_code=idn.country_code,
                    )
                )

                fid.write(
                    "\"MARKER NAME\"         : {{ 0: \"{station:4}00{country_code:3}\" }}\n".format(
                            station=station.upper(),
                            country_code=idn.country_code,
                    )
                )

            # Write 4-digit station name
            else:
                fid.write(
                    "0 - {station:4}\n".format(
                        station=station.upper(),
                    )
                )

                fid.write(
                    "\"MARKER NAME\"         : {{ 0: \"{station:4}\" }}\n".format(
                            station=station.upper(),
                    )   
                )

            fid.write(
                "\"MARKER NUMBER\"       : {{ 0: \"{domes:9}\" }}\n".format(
                        domes= idn.domes if idn.domes else "",
                )   
            )

            # TODO: Length of observer name is limited.
            #fid.write(
            #    "\"OBSERVER / AGENCY\"   : {{ 0: \"{agency}\" }}\n".format(
            #            agency=idn.agency,
            #    )
            #    
            #)
            
            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # \"REC # / TYPE / VERS\" + 19970127:00000  20000426:00000  : { 0: \"3511A10131\", 1: \"TRIMBLE 4000SSI\", 2: \"7.28\" }
            for date, rcv in site_info[station]["receiver"].history.items():
                fid.write(
                    "\"REC # / TYPE / VERS\" + {date_from:15} {date_to:15} : {{ 0: \"{rcv_serial}\", 1: \"{rcv_type}\", 2: \"{firmware}\" }}\n".format(
                        date_from=_get_yyyyddd_sssss(date[0]),
                        date_to=_get_yyyyddd_sssss(date[1]),
                        rcv_serial=rcv.serial_number,
                        rcv_type=rcv.type,
                        firmware=rcv.firmware,                        
                    )
                )              

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # \"ANT # / TYPE\" + 19980613:00000  20080624:00000  : { 0: \"220098660\", 1: \"TRM29659.00\", 2: \"SCIS\" }
            for date, ant in site_info[station]["antenna"].history.items():
                fid.write(
                    "\"ANT # / TYPE\" + {date_from:15} {date_to:15} : {{ 0: \"{ant_serial}\", 1: \"{ant_type}\", 2: \"{radome_type}\" }}\n".format(
                        date_from=_get_yyyyddd_sssss(date[0]),
                        date_to=_get_yyyyddd_sssss(date[1]),
                        ant_serial=ant.serial_number,
                        ant_type=ant.type,
                        radome_type="NONE" if not ant.radome_type else ant.radome_type,                        
                    )
                )

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # "APPROX POSITION XYZ" + 19970127:000000 20090908:000000 : { 0: "2938027.606", 1: "319096.208", 2: "5633413.781" }
            if (
                "site_coord" in site_info[station]
            ):
                if site_info[station]["site_coord"].history:
                    for date, crd in site_info[station]["site_coord"].history.items():
                        fid.write(
                            "\"APPROX POSITION XYZ\" +  {date_from:15} {date_to:15} : {{ 0: \"{x}\", 1: \"{y}\", 2: \"{z}\" }}\n".format(
                                date_from=_get_yyyyddd_sssss(date[0]),
                                date_to=_get_yyyyddd_sssss(date[1]),
                                x=crd.pos.trs.x,
                                y=crd.pos.trs.y,
                                z=crd.pos.trs.z,                     
                            )
                        )

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # "ANTENNA: DELTA H/E/N" + 19970127:000000 00000000:000000 : { 0: "5.536",  1: "0.005" ,  2: "-0.001"}
            for date, ecc in site_info[station]["eccentricity"].history.items():
                fid.write(
                    "\"ANTENNA: DELTA H/E/N\" + {date_from:15} {date_to:15} : {{ 0: \"{up}\", 1: \"{east}\", 2: \"{north}\" }}\n".format(
                        date_from=_get_yyyyddd_sssss(date[0]),
                        date_to=_get_yyyyddd_sssss(date[1]),
                        up=ecc.up,
                        east=ecc.east,
                        north=ecc.north,                        
                    )
                )

#
# AUXILIARY FUNCTIONS
#                   
def _get_yyyyddd_sssss(date: datetime) -> str:
    """Get date format <YYYYMMDD:SSSSS>

    Args:
        date:   Date
    
    Returns:
        Date in format  <YYYYMMDD:SSSSS>
    """
    seconds_per_day = str(int(date.hour * 3600 + date.minute * 60 + date.second)).zfill(5)
    datetime_limit = datetime(9999, 12, 31, 23, 59, 59, 999999)

    if date == datetime_limit:
        yyyymmdd_sssss="00000000:00000"
    else:
        yyyymmdd_sssss=f"{date.strftime('%Y%j')}:{seconds_per_day}"

    return yyyymmdd_sssss
