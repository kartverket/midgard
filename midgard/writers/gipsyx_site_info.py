"""Write site information file for GipsyX

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
def gipsyx_site_info(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
) -> None:
    """Write site information file for GipsyX

    Args:
        file_path:       File path of site information GipsyX output file
        site_info:       Dictionary with station information, whereby station name is the key and a dictionary with 
                         site information the value.
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # BJOS  ANT    2009-12-09 00:00:00  TRM41249.00 NONE   0.000000e+00   0.000000e+00   0.000000e+00  # 12682
    # BJOS  ANT    2013-01-22 00:00:00  TRM41249.00 NONE   0.000000e+00   0.000000e+00   0.000000e+00  # 12682
    # BJOS  ID  97103M001  Bjørnøya, NO
    # BJOS  RX     2009-12-09 00:00:00  TRIMBLE MS750 # 0220 1.53
    # BJOS  RX     2013-01-22 00:00:00  TRIMBLE MS750 # 0220 1.53
    # BJOS  RX     2016-02-12 00:00:00  TRIMBLE NETR8 # 4923 4.87
    # BJOS  RX     2017-04-04 00:00:00  TRIMBLE NETR8 # 4923 48.01
    # BJOS  STATE  2009-12-09 00:00:00  1.616317468e+06         5.56586746e+05         6.124236590e+06       -0.016700e+00           0.008900e+00           0.003300e+00

    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:

        fid.write("KEYWORDS: ANT END ID POSTSEISMIC RX STATE\n")
        for station in sorted(site_info.keys()):

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # BJOS  ID  97103M001  Bjørnøya, NO
            idn = site_info[station]["identifier"]
            fid.write(
                "{station:6}{id_:4}{domes:9}  {name}, {country}\n".format(
                    station=station.upper(),
                    id_="ID",
                    domes=idn.domes if idn.domes else "UNKNOWN",
                    name=idn.name if idn.name else "",
                    country=idn.country if idn.country else "",
                )
            )
              
            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # BJOS  ANT    2009-12-09 00:00:00  TRM41249.00 NONE   0.000000e+00   0.000000e+00   0.000000e+00  # 12682
            
            # Get antenna information related to dates of ANTENNA changes
            ant_data = dict()
            for date, ant in site_info[station]["antenna"].history.items():
                
                ecc = _get_eccentricity(date[0], site_info[station]["eccentricity"])
   
                line = (
                    "{station:6}{id_:7}{date_from:21}{type_} {radome_type}{east:>15.6e}{north:>15.6e}{up:>15.6e}{serial}\n".format(
                        station=station.upper(),
                        id_="ANT",
                        date_from=date[0].strftime("%Y-%m-%d %H:%M:%S"),
                        type_=ant.type,
                        radome_type="NONE" if not ant.radome_type else ant.radome_type,
                        east=ecc.east, #TODO: when ecc is given as xyz
                        north=ecc.north,
                        up=ecc.up,
                        serial=f"  # {ant.serial_number}",  # TODO log information?
                    )
                )
                
                ant_data.update({date[0]: line})

            # Add additional antenna information related to dates of ECCENTRICITY changes                
            for date, ecc in site_info[station]["eccentricity"].history.items():
                
                if date not in ant_data.keys():
                    
                    ant = _get_antenna(date[0], site_info[station]["antenna"])
                            
                    line = (
                        "{station:6}{id_:7}{date_from:21}{type_} {radome_type}{east:>15.6e}{north:>15.6e}{up:>15.6e}{serial}\n".format(
                            station=station.upper(),
                            id_="ANT",
                            date_from=date[0].strftime("%Y-%m-%d %H:%M:%S"),
                            type_=ant.type,
                            radome_type="NONE" if not ant.radome_type else ant.radome_type,
                            east=ecc.east, #TODO: when ecc is given as xyz
                            north=ecc.north,
                            up=ecc.up,
                            serial=f"  # {ant.serial_number}",  # TODO log information?
                        )
                    )
                
                    ant_data.update({date[0]: line})
                    
            # Write antenna information to file
            for date in sorted(ant_data.keys()):
                fid.write(ant_data[date])

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # BJOS  RX     2009-12-09 00:00:00  TRIMBLE MS750 # 0220 1.53
            for date, rcv in site_info[station]["receiver"].history.items():
                fid.write(
                    "{station:6}{id_:7}{date_from:21}{type_}{serial}\n".format(
                        station=station.upper(),
                        id_="RX",
                        date_from=date[0].strftime("%Y-%m-%d %H:%M:%S"),
                        type_=rcv.type,
                        serial=f" # {rcv.serial_number} {rcv.firmware}",
                    )
                )

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # BJOS  STATE  2009-12-09 00:00:00  1.616317468e+06         5.56586746e+05         6.124236590e+06       -0.016700e+00           0.008900e+00           0.003300e+00
            if (
                "site_coord" in site_info[station]
            ):
                if site_info[station]["site_coord"].history:
                    for date, crd in site_info[station]["site_coord"].history.items():
                        fid.write(
                            "{station:6}{id_:7}{date_from:21}{x:17.9e}{y:23.9e}{z:23.9e}{vx:23.9e}{vy:23.9e}{vz:23.9e}\n".format(
                                station=station.upper(),
                                id_="STATE",
                                date_from=date[0].strftime("%Y-%m-%d %H:%M:%S"),
                                x=crd.pos.trs.x,
                                y=crd.pos.trs.y,
                                z=crd.pos.trs.z,
                                vx=crd.vel[0], 
                                vy=crd.vel[1], 
                                vz=crd.vel[2], 
                            )
                        )


#
# AUXILIARY FUNCTIONS
#                   
def _get_antenna(date: datetime, antenna: "AntennaHistory") -> "Antenna":
    """Get antenna information for a given date

    Args:
        date:    Date
        antenna: Antenna history object for a given station
        
    Returns:
        Antenna object for given date
    """
    for (date_from, date_to), ant in sorted(antenna.history.items()):
        if date < date_from:
            log.warn(f"Date of first antenna and eccentricity site information for station {ant.station.upper()} is "
                     f"not equal (Antenna: {date_from.strftime('%Y-%m-%d')}/Eccentricity: "
                     f"{date.strftime('%Y-%m-%d')})."
             )
            return ant
        
        if date_from <= date < date_to:
            return ant
                        

def _get_eccentricity(date: datetime, eccentricity: "EccentricityHistory") -> "Eccentricity":
    """Get eccentricity for a given date

    Args:
        date:         Date
        eccentricity: Eccentricity history object for a given station
        
    Returns:
        Eccentricity object for given date
    """
    for (date_from, date_to), ecc in sorted(eccentricity.history.items()):
        if date < date_from:
            log.warn(f"Date of first antenna and eccentricity site information for station {ecc.station.upper()} is "
                     f"not equal (Antenna: {date_from.strftime('%Y-%m-%d')}/Eccentricity: "
                     f"{date.strftime('%Y-%m-%d')})."
             )
            return ecc
        
        if date_from <= date < date_to:
            return ecc
