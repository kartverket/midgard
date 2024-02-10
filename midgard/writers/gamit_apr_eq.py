"""Write apr and eq file for GAMIT

Description:
------------


"""

# Standard library imports
from datetime import datetime
from pathlib import PosixPath, Path
from typing import Any, Dict

# Third party imports
import numpy as np

# Midgard imports
from midgard.dev import log, plugins
from midgard.files import files

@plugins.register
def gamit_apr_eq(
        apr_path: PosixPath, 
        eq_path: PosixPath,
        site_info: Dict[str, Any],
        ref_frame: str,
) -> None:
    """Write apr and eq file for GAMIT

    Args:
        apr_path:    File path of GAMIT *.apr file
        eq_path:     File path of GAMIT *.eq file      
        site_info:   Dictionary with station information, whereby station name is the key and a dictionary with 
                     site information the value.           
        ref_frame:   Reference frame name of site coordinates (e.g. IGb14)
    """
    
    ### Example of apr file
    # Combined ITRF/IGS/EPN/NGS solutions expressed in IGS realization of ITRF2014
    # Created with combine_ITRF2014.sh by Mike Floyd on 2018-07-15
    #+REFERENCE_FRAME IGS14
    # 0194_GPS -3766965.51519  3211877.12142  4008334.28035  -0.01140  -0.00413  -0.00472 2010.0     0.00082  0.00069  0.00070  0.00006  0.00005  0.00006 21752S001 from ITRF2014
    # 0194_2PS -3766965.50247  3211877.11780  4008334.27947  -0.01140  -0.00413  -0.00472 2010.0     0.00078  0.00065  0.00065  0.00006  0.00005  0.00006 21752S001 from ITRF2014
    # ...
    # EXTENDED YSSK_4PS EXP 2006 11 15 11 14  940.7  0.00000  0.02093  0.00000 12329M003 from ITRF2014
    # EXTENDED YSSK_5PS EXP 2003 09 25 19 50  560.8 -0.01241  0.00000  0.00000 12329M003 from ITRF2014
    # EXTENDED YSSK_5PS EXP 2006 11 15 11 14   93.7  0.00000  0.00548  0.00000 12329M003 from ITRF2014

    ### Example of eq file
    # rename REYK     REYK_GPS 1980 01 01 00 00 2000 06 17 15 00
    # rename REYK     REYK_2PS 2000 06 17 15 00 2000 06 21 00 00
    # rename REYK     REYK_3PS 2000 06 21 00 00 2003 06 13 15 00
    # rename REYK     REYK_4PS 2003 06 13 15 00 2007 09 20 16 00    
    
    log.info(f"Write file {apr_path} and {eq_path}")

    with files.open(apr_path, create_dirs=True, mode="wt") as fid_apr, \
        files.open(eq_path, create_dirs=True, mode="wt") as fid_eq:
    
        # Write header
        fid_apr.write("# Combined Site coordinate and velocity information\n")
        fid_apr.write(f"# Created by Midgard, {datetime.now():%Y-%m-%d %H:%M}\n")
        fid_apr.write(f"+REFERENCE_FRAME {ref_frame}\n")

        for station, values in site_info.items():
            last_site_coord = False
            sc_iter = iter(values["site_coord"])
            source_path = Path(values["site_coord"].source_path).stem
            
            try:
                sc = next(sc_iter)
                num = 1
            except StopIteration:
                last_site_coord = True
            
            while (not last_site_coord):
                if num == 1:
                    point = "GPS"
                elif num < 10:
                    point = f"{num}PS"
                elif num < 100:
                    point = f"{num}S"
                else:
                    point = f"{num}"

                ident = f"{sc.station.upper()}_{point}"
                
                x = sc.pos[0] or np.nan
                y = sc.pos[1] or np.nan
                z = sc.pos[2] or np.nan

                x_sig = sc.pos_sigma[0] or np.nan
                y_sig = sc.pos_sigma[1] or np.nan
                z_sig = sc.pos_sigma[2] or np.nan

                vx = sc.vel[0] or np.nan
                vy = sc.vel[1] or np.nan
                vz = sc.vel[2] or np.nan

                vx_sig = sc.vel_sigma[0] or np.nan
                vy_sig = sc.vel_sigma[1] or np.nan
                vz_sig = sc.vel_sigma[2] or np.nan

                epoch = sc.ref_epoch.decimalyear if sc.ref_epoch else 0
                comment = f"{sc.system} from {sc.source} ({source_path})"

                # 0194_GPS -3766965.51519  3211877.12142  4008334.28035  -0.01140  -0.00413  -0.00472 2010.0     0.00082  0.00069  0.00070  0.00006  0.00005  0.00006 21752S001 from ITRF2014
                fid_apr.write(f" {ident:8} {x:14.5f} {y:14.5f} {z:14.5f} {vx:9.5f} {vy:9.5f} {vz:9.5f} {epoch:6.1f}    ")
                fid_apr.write(f"{x_sig:8.5f} {y_sig:8.5f} {z_sig:8.5f} {vx_sig:8.5f} {vy_sig:8.5f} {vz_sig:8.5f} {comment}\n")
                
                start = sc.date_from.strftime("%Y %m %d %H %M")
                end = sc.date_to.strftime("%Y %m %d %H %M")

                # rename REYK     REYK_GPS 1980 01 01 00 00 2000 06 17 15 00
                fid_eq.write(f" rename {station.upper():8} {ident:8} {start} {end}\n")
                try:
                    sc = next(sc_iter)
                    num += 1
                except StopIteration:
                    last_site_coord = True
                    
        
