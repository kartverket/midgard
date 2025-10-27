"""Write Bernese station information file in *.STA format

Description:
------------

"""
# Standard library imports
from datetime import datetime
import itertools
from pathlib import PosixPath
import re
from typing import Any, Dict, List, Tuple, Union

# Midgard imports
from midgard import parsers
from midgard.dev import log, plugins
from midgard.files import files


@plugins.register
def bernese_sta(
        file_path: PosixPath, 
        site_info: Dict[str, Any],
        rename_station: Dict[str, str] = dict(),
        event_path: Union[PosixPath, None] = None,
        agency: str = "UNKNOWN",
        skip_firmware: bool = False,
        use_first_common_date: bool = True,
) -> None:
    """Write Bernese station information file in *.STA format

    Args:
        file_path:       File path of Bernese *.STA output file
        site_info:       Dictionary with station information, whereby station name is the key and a dictionary with 
                         site information the value.
        rename_station:  Dictionary with official 4-digit station name as key and the alternative name as value. This 
                         information is used in the "RENAMING OF STATIONS" section in Bernese *.STA file. This can be
                         necessary if the used 4-digit station names are not unique.
        event_path:      File path of event file with additional event 
        agency:          Agency which uses this Bernese station information file for processing
        skip_firmware:   Skip firmware changes by generating "TYPE 002: STATION INFORMATION" block
        use_first_common_date: Use first common date entry given by receiver, antenna and eccentricity properties. It  
                         can happen, that the first date entry is inconsistent for these properties. In this case the
                         first common date entry of one of these properties is used in the BERNESE STA file. The 
                         alternative is to skip date entries, which does not fit into the given date period. 
    """

    # EXAMPLE:
    #
    # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
    # BERNESE V.5.2 STA FILE FOR EPN PROCESSING                        02-Jun-20 08:42
    # --------------------------------------------------------------------------------
    #
    # FORMAT VERSION: 1.01
    # TECHNIQUE:      GNSS
    #
    # TYPE 001: RENAMING OF STATIONS
    # ------------------------------
    #
    # STATION NAME          FLG          FROM                   TO         OLD STATION NAME      REMARK
    # ****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ************************
    # ADAC 10337M001        001  1980 01 06 00 00 00  2099 12 31 00 00 00  ADAC*                 From ADAC0540.13O
    # ALES 10336M001        001  1980 01 06 00 00 00  2099 12 31 00 00 00  ALES*                 From ALES0540.13O
    # ANDO 10333M001        001  1980 01 06 00 00 00  2099 12 31 00 00 00  ANDO*                 From ANDO0540.13O

    log.info(f"Write file {file_path}")

    with files.open(file_path, create_dirs=True, mode="wt") as fid:
        
        # Write header
        fid.write(_get_header(agency))
                
        #
        # TYPE 001: RENAMING OF STATIONS
        #
        fid.write(_get_interline_header("TYPE 001: RENAMING OF STATIONS"))
        fid.write("\n")
        fid.write("STATION NAME          FLG          FROM                   TO         OLD STATION NAME      REMARK\n")
        fid.write("****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ************************\n")
        for sta in sorted(site_info.keys()):
            
            identifier = site_info[sta]['identifier']
            if identifier.source == "sestation":
                remark = "From NMA seStation API"
            elif identifier.source == "snx":
                remark = f"From {identifier.source_path.name} file"
            elif identifier.source == "m3g":
                remark = "From gnss-metadata.eu M3G API"
            else:
                log.fatal(f"Source {identifier.source} is not defined.")

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1
            # ADAC 10337M001        001  1980 01 06 00 00 00  2099 12 31 00 00 00  ADAC*                 From ADAC0540.13O 
            fid.write(
                "{station:4} {domes:10}{flag:>10}{date_from:>21}{date_to:>21}  {old_station:20}  {remark}\n".format(
                    station=sta.upper(),
                    domes="" if identifier.domes is None else identifier.domes,
                    flag="001",
                    date_from=site_info[sta]['antenna'].date_from[0].strftime("%Y %m %d %H %M %S"),
                    date_to=site_info[sta]['antenna'].date_to[-1].strftime("%Y %m %d %H %M %S"),
                    old_station= rename_station[sta].upper() if sta in rename_station.keys() else sta.upper(),
                    remark=remark,
                )
            )
        fid.write("\n")
                
        #
        # TYPE 002: STATION INFORMATION
        #
        fid.write(_get_interline_header("TYPE 002: STATION INFORMATION"))
        fid.write("\n")
        fid.write("STATION NAME          FLG          FROM                   TO         RECEIVER TYPE         RECEIVER SERIAL NBR   REC #   ANTENNA TYPE          ANTENNA SERIAL NBR    ANT #    NORTH      EAST      UP     AZIMUTH  LONG NAME  DESCRIPTION             REMARK\n")
        fid.write("****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ********************  ******  ********************  ********************  ******  ***.****  ***.****  ***.****  ****.*  *********  **********************  ************************\n")
        for sta in sorted(site_info.keys()):
                        
            events, first_property_date = _get_events(
                            site_info, 
                            sta,
                            skip_firmware=skip_firmware,
                            use_first_common_date=use_first_common_date,
            )
            identifier = site_info[sta]['identifier']
            ant_hist= site_info[sta]["antenna"].history
            ecc_hist = site_info[sta]["eccentricity"].history
            rcv_hist = site_info[sta]["receiver"].history

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----+----9----+----0----+----1----+----2----+----3----+----4----+----5
            # BRUX                  001  2021 04 20 08 33 00  2099 12 31 00 00 00  SEPT POLARX5TR        3057609                57609  JAVRINGANT_DM   SCIS  999999                999999    0.0010    0.0000    0.4689     0.0  BRUX00BEL  Brussels, BEL           5.4.0
            # ****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ********************  ******  ********************  ********************  ******  ***.****  ***.****  ***.****  ****.*  *********  **********************  ************************
            for date_from , date_to in _pairwise(sorted(events.keys())):

                if first_property_date:
                    if date_from < first_property_date:
                        continue
                
                rcv = _get_object_for_date(date_from, rcv_hist)                
                if not rcv:
                    log.warn(f"Receiver type is not defined for station {sta.upper()} and time {date_from.strftime('%d-%b-%y %H:%M:%S')}. Skip station time entry.")
                    continue
             
                ant = _get_object_for_date(date_from, ant_hist)
                if not ant:
                    log.warn(f"Antenna type is not defined for station {sta.upper()} and time {date_from.strftime('%d-%b-%y %H:%M:%S')}. Skip station time entry.")
                    continue
    
                ecc = _get_object_for_date(date_from, ecc_hist)
                if not ecc:
                    log.warn(f"Eccentricity is not defined for station {sta.upper()} and time {date_from.strftime('%d-%b-%y %H:%M:%S')}. Skip station time entry.")
                    continue
                
                fid.write(
                    "{station:4s} {domes:10s}{flag:>10s}{date_from:>21s}{date_to:>21s}  {rcv:20.20s}  {rcv_serial:<20.20s}  {rcv_serial_short:>6.6s}  {ant:15.15s} {radome:4.4s}  {ant_serial:<20.20s}  {ant_serial_short:>6.6s}  {north:>8.4f}  {east:>8.4f}  {up:>8.4f}  {azimuth:>6.1f}  {long_name:>8s}  {description:22.22}  {remark}\n".format(
                        station=sta.upper(),
                        domes="" if identifier.domes is None else identifier.domes,
                        flag="001",
                        date_from=date_from.strftime("%Y %m %d %H %M %S"),
                        date_to=date_to.strftime("%Y %m %d %H %M %S"),
                        rcv=rcv.type,
                        rcv_serial=rcv.serial_number,
                        rcv_serial_short=re.sub("[^0-9]", "", rcv.serial_number)[-6:],
                        ant=ant.type,
                        radome=ant.radome_type if ant.radome_type else "NONE",
                        ant_serial=ant.serial_number,
                        ant_serial_short=re.sub("[^0-9]", "", ant.serial_number)[-5:] if ant.calibration else "999999",
                        north=ecc.north,
                        east=ecc.east,
                        up=ecc.up,
                        azimuth=0.0,
                        long_name=f"{sta.upper()}00{identifier.country_code.upper()}" if identifier.country_code else f"{sta.upper()}00XXX",
                        description= f"{identifier.name}, {identifier.country_code}" if identifier.country_code else identifier.name,
                        remark=rcv.firmware,
                    )
                )
        fid.write("\n")
        
        #
        # TYPE 003: HANDLING OF STATION PROBLEMS
        #
        fid.write(_get_interline_header("TYPE 003: HANDLING OF STATION PROBLEMS"))
        fid.write("\n")
        fid.write("STATION NAME          FLG          FROM                   TO         REMARK\n")
        fid.write("****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ************************************************************\n")


        for sta in sorted(site_info.keys()):
            
            identifier = site_info[sta]['identifier']
            events, first_property_date = _get_events(
                            site_info, 
                            sta, 
                            skip_firmware=True, # Skip firmware update dates, only interested in receiver type changes.
                            use_first_common_date=use_first_common_date, 
                            event_path=event_path, # Read file with events and add them to dates.
            ) 
            del events[sorted(events.keys())[0]]  # First date is the installation date and should be rejected as problematic date.
            del events[sorted(events.keys())[-1]] # On last date are not equipment changes done.

            # ----+----1----+----2----+----3----+----4----+----5----+----6----+----7----+----8----
            # STAS 10330M001        001  2007 05 02 00 00 00  2007 06 30 00 00 00  DEFEKT ANTENNE
            for date, items in sorted(events.items()):

                if first_property_date:
                    if date < first_property_date:
                        continue
                                
                fid.write(
                    "{station:4s} {domes:10s}{flag:>10s}{date_from:>21s}{date_to:>21s}  {remark}\n".format(
                        station=sta.upper(),
                        domes="" if identifier.domes is None else identifier.domes,
                        flag="001",
                        date_from=date.strftime("%Y %m %d %H %M %S"),
                        date_to=items["date_to"],
                        remark=items["description"],
                    )
                )
        
        #
        # TYPE 004: STATION COORDINATES AND VELOCITIES (ADDNEQ)
        #
        fid.write(_get_interline_header("TYPE 004: STATION COORDINATES AND VELOCITIES (ADDNEQ)"))
        fid.write("                                            RELATIVE CONSTR. POSITION     RELATIVE CONSTR. VELOCITY\n")
        fid.write("STATION NAME 1        STATION NAME 2        NORTH     EAST      UP        NORTH     EAST      UP\n")
        fid.write("****************      ****************      **.*****  **.*****  **.*****  **.*****  **.*****  **.*****\n") 
      
        #
        # TYPE 005: HANDLING STATION TYPES
        #
        fid.write(_get_interline_header("TYPE 005: HANDLING STATION TYPES"))
        fid.write("STATION NAME          FLG  FROM                 TO                   MARKER TYPE           REMARK\n")
        fid.write("****************      ***  YYYY MM DD HH MM SS  YYYY MM DD HH MM SS  ********************  ************************\n")
             
        #
        # TYPE/FLAG  DESCRIPTION
        #
        fid.write("\n\n\n")
        fid.write(_get_interline_header("TYPE/FLAG  DESCRIPTION"))
        fid.write("\n")
        fid.write("001 001: RENAME STATION IN ALL PROGRAMS. NEW NAME IS USED FOR ALL FLAGS BELOW\n")
        fid.write("001 002: RENAME STATION RXOBV3. WILDCARDS ALLOWED. NEW NAME IS USED FOR ALL FLAGS BELOW\n")
        fid.write("001 003: RENAME STATION IN ADDNEQ. NEW NAME IS USED FOR ALL FLAGS BELOW\n\n")
        fid.write("002 001: STATION INFORMATION RECORD\n\n")
        fid.write("003 001: EXCLUDE STATION IN ALL PROGRAMS\n")
        fid.write("003 003: EXCLUDE STATION IN ADDNEQ (PREELIMINATION)\n")
        fid.write("003 011: STATION NOT BE USED FOR FIXING OR CONSTRAINING\n")


#
# AUXILIARY FUNCTIONS
#
                
def _get_header(agency: str) -> str:
    """Get header
        
    Args:
        agency:  Agency which uses this Bernese station information file for processing
        
    Return:
        Header as string
    """
    solution=f"BERNESE V.5.4 STA FILE FOR {agency.upper()} PROCESSING"
    return (f"{solution:64s} {datetime.now().strftime('%d-%b-%y %H:%M'):s}\n"
            f"{'-'*80}\n\n"
            "FORMAT VERSION: 1.01\n"
            "TECHNIQUE:      GNSS\n"        
    )      


def _get_interline_header(line: str) -> str:
    """Get interline header

    Args:
        line:        Line to write as header
        
    Return:
        Header as string
    """
    
    return (f"\n{line}\n"
            f"{'-'*len(line)}\n"      
    )


def _get_object_for_date(
                date: datetime,
                history: Dict[str, Any],
) -> Dict[Tuple[datetime, datetime], Any]:
    """Get antenna, receiver or eccentricity object for a given date based on object history

    Args:
        date:     Date
        history:  Antenna, receiver or eccentricity history dictionary (e.g. 
                  site_info[station]["antenna"].history)


        first_property_date: First common property date, which should be used for BERNESE_STA file generation.
        
    Returns:
        Antenna, receiver or eccentricity object and updated date 
    """
    for (date_from, date_to), object_ in sorted(history.items()):

        # Set hour, minute and second to zero. This avoids possible data gaps by changing the GNSS equipment. Data gaps
        # can lead to missing receiver or antenna information in a certain time span. 
        date_from = datetime(date_from.year, date_from.month, date_from.day)
        date_to = datetime(date_to.year, date_to.month, date_to.day)
                
        if date_from <= date < date_to:
            return object_
        
        
def _get_events(
        site_info: Dict[str, Any], 
        station: str, 
        skip_firmware: bool = False,
        use_first_common_date: bool = True,
        event_path: Union[None, PosixPath] = None,
    ) -> Tuple[Dict[datetime, List[str]], datetime]:
    """Get events for given station needed for "station information" or "handling of station problems" section

    The "station information" section of Bernese files includes receiver, antenna and eccentricity information. Changes
    in each property has to be shown in this section. The generated event list represent relevant changes.
    
    An event file is read in case of station problems, which adds beside equipment changes events also information  
    about other events to "dates" dictionary.
    
    The "events" dictionary looks like:
    
            events = { 
                <date_from> {
                        date_to: <date>,
                        description: <station problem description>,
                        property: [<property>, ...],
                },
                <date_from> {
                        date_to: <date>,
                        description: <station problem description>,
                        property: [<property>, ...],
                },
                ...
            }
                        
    
    Args:
        site_info:      Dictionary with station information, whereby station name is the key and a dictionary with site
                        information the value.
        station:        Station name
        skip_firmware:  Skip firmware changes by generating dates 
        use_first_common_date: Use first common date entry given by receiver, antenna and eccentricity properties. It  
                        can happen, that the first date entry is inconsistent for these properties. In this case the
                        first common date entry of one of these properties is used in the BERNESE STA file. The 
                        alternative is to skip date entries, which does not fit into the given date period.
        event_path:     File path of event file with additional event
        
    Returns:
        Tuple with a dictionary with start dates of events as keys and a dictionary with items as values. The items
        includes end date ("date_to"), "description" and "property" information. In addition the tuple includes the
        first property date, which should be used for BERNESE_STA file generation.
    """
    events = dict()
    first_property_date = None
    first_property_date_entry = {}
    former_ant_type = None
    former_ant_serial_number = None
    former_radome_type = None
    
    ant_hist = site_info[station]["antenna"].history
    
    if skip_firmware:
        former_rcv_type = None
        former_rcv_serial_number = None
        rcv_hist = site_info[station]["receiver"].history
    
    # Add equipment changes events
    for property_ in ["receiver", "antenna", "eccentricity"]:
        for date, _ in site_info[station][property_].history.items():
            
            # Skip firmware changes
            if skip_firmware and property_ == "receiver":
                rcv = _get_object_for_date(date[0], rcv_hist)
                if rcv.type == former_rcv_type and rcv.serial_number == former_rcv_serial_number:
                    log.debug(f"Skip firmware update for station {station.upper()} on date "
                             f"{date[0].strftime('%d-%b-%y %H:%M:%S')}.")
                    continue
                else:
                    former_rcv_type = rcv.type
                    former_rcv_serial_number = rcv.serial_number
                    
            # Detect if antenna and/or radome type is changed
            if property_ == "antenna":
                ant = _get_object_for_date(date[0], ant_hist)
                if ant.type == former_ant_type and ant.serial_number == former_ant_serial_number:
                    if not ant.radome_type == former_radome_type:
                        property_ = "radome"
                        
                former_ant_type = ant.type
                former_ant_serial_number = ant.serial_number
                former_radome_type = ant.radome_type

            # Save first date entry for each property
            if property_ not in first_property_date_entry.keys() and not property_=="radome":  # First use of radome can be different related to antenna installation.
                first_property_date_entry[property_] = date[0]

            # Append new date
            if date[0] in events.keys():
                
                if  property_ in events[date[0]]["property"]:
                    log.warn(f"{property_.capitalize()} information is registrated twice for station "
                             f"{station.upper()} on date {date[0].strftime('%d-%b-%y %H:%M:%S')}.")
                    continue
                events[date[0]]["property"].append(property_)
            else:
                events.update({
                    date[0]: {
                        "date_to": date[0].strftime("%Y %m %d 23 59 59"),
                        "property": [property_],
                    }
                })

    # Add last date (Note: This is needed for getting last information at "station information" section.)
    events.update({date[1]: {}})
   
    # Check if first date entry of each property is consistent
    first_property_dates = set(first_property_date_entry.values())
    if len(first_property_dates) > 1:
        date_log_msg = [f"{k}: {v.strftime('%Y-%m-%d %H:%M:%S')}" for k,v in first_property_date_entry.items()]
        log.warn(f"First date of given station information entries is inconsistent for station {station.upper()} "
                 f"({', '.join(date_log_msg)}).")

        # Apply first date entry for all properties
        if use_first_common_date:
            first_property_date = max(first_property_dates)
            log.warn(f"Date {first_property_date} is used as starting date for all properties (like receiver, antenna or "
                     f"eccentricity information) for station {station.upper()} .")

            ## Note: All first property dates larger than first date should be changed.
            #change_dates = [v for v in first_property_dates if v > first_date] 
            #for date in events.keys():
            #    if date in changes_dates:
            #        events[date]
                 
    # Add addtional events read from file
    if event_path:
        events_from_file = _read_events_from_file(station, event_path)
        if events_from_file:
            events.update(events_from_file) 
        
    # Add description based on given properties    
    for date, items in events.items():
        if items:
            if not "description" in items:
                events[date]["description"] = _replace_last(f"New {', '.join(items['property'])}", ",", " and")
                         
    return events, first_property_date
    
#TODO: Should maybe be moved to a library.    
def _pairwise(iterable: Any) -> zip:
    """Generate pairwise iterables, whereby the current and next iterable is returned
    
    Args:
        iterable: Iterables
        
    Return:
        Zip object with current and next iterable
    """
    current, next_ = itertools.tee(iterable)
    next(next_, None)

    return zip(current, next_)


def _read_events_from_file(station: str, file_path: PosixPath) -> Dict[datetime, Dict[str, Any]]:
    """Read events related to observations periods, which should be removed
    
    Args:
        station:    Station name
        file_path:  File path of event file with additional events
        
    Returns:
        Dictionary with start dates of event as key and a dictionary as values with end dates and event description 
        information
    """
    events = dict()
    
    # Get events
    if not file_path.exists():
        log.fatal(f"File {file_path} does not exist.")
    p = parsers.parse_file(parser_name="sinex_events", file_path=file_path)
    file_events = p.as_dict()
    
    if station not in file_events:
        return events
        
    # Save events in events dictionary
    for event in file_events[station]["solution_event"]:
        if event["event_code"].startswith("RMV"):
            events.update({ 
                event["start_time"]: {
                    "date_to": event["end_time"].strftime("%Y %m %d %H %M %S"),
                    "description":  event["description"],
                }
            })
            
    return events


def _replace_last(string: str, old: str, new: str) -> str:
    """Replace last occurence of a substring in string

    Args:
        string:   Original string
        old:      Old substring
        new:      New substring, which should replace the old substring
        
    Returns:
        Updated string
    """
    return new.join(string.rsplit(old, 1))
