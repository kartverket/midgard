"""A parser for reading satellite metadata information from SINEX format

Example:
--------

    from midgard import parsers
    p = parsers.parse_file(parser_name='sinex_satellite_metadata', file_path='sinex_satellite_metadata')
    data = p.as_dict()

Description:
------------

Reads station related information (e.g. approximated station coordinates, receiver and antenna type, station 
eccentricities, ...) from files in SINEX format. Following blocks are read:

            FILE/REFERENCE
            FILE/COMMENT   
            SATELLITE/IDENTIFIER
            SATELLITE/PLANE
            SATELLITE/PRN
            SATELLITE/FREQUENCY_CHANNEL
            SATELLITE/MASS
            SATELLITE/COM
            SATELLITE/ECCENTRICITY
            SATELLITE/TX_POWER

"""
# Standard library imports
from typing import Callable, List
import numpy as np

# Midgard imports
from midgard.data import dataset
from midgard.dev import plugins

# Where imports
from midgard.parsers._parser_sinex import SinexParser


@plugins.register
class SinexMetaParser(SinexParser):
    """A parser for reading satellite metadata information from SINEX format

    satellite - Satellite dictionary, whereby keys are the satellite identifiers and values are a satellite entry
           dictionary with the keys 'satellite_identifier', 'satellite_plane', 'satellite_prn',
           'satellite_frequency_channel', 'satellite_mass', 'satellite_com', 'satellite_eccentricity',
           and 'satellite_tx_power'. The satellite dictionary has following structure:

              self.satellite[satellite] = { 
                'satellite_identifier':         {}, # SATELLITE/IDENTIFIER block information
                'satellite_plane':              [], # SATELLITE/PLANE block information
                'satellite_prn':                [], # SATELLITE/PRN block information
                'satellite_frequency_channel':  [], # SATELLITE/FREQUENCY_CHANNEL block information
                'satellite_mass':               [], # SATELLITE/MASS block information
                'satellite_com':                [], # SATELLITE/COM block information
                'satellite_eccentricity':       {}, # SATELLITE/ECCENTRICITY block information
                'satellite_tx_power':           [], # SATELLITE/TX_POWER block information
              }

           with the site entry dictionary entries

              satellite_identifier              = { 
                                        'svn':              svn,
                                        'cospar_id':        cospar_id,
                                        'satcat':           satcat,
                                        'block':            block,
                                        'comment':          comment }

              satellite_plane[ii]               = { 
                                        'svn':              svn,
                                        'valid_from':       valid_from,
                                        'valid_to':         valid_to,
                                        'plane':            plane,
                                        'slot':             slot,
                                        'comment':          comment }

              satellite_prn[ii]                 = { 
                                        'svn':              svn,
                                        'valid_from':       valid_from,
                                        'valid_to':         valid_to,
                                        'prn':              prn,
                                        'comment':          comment }

              satellite_frequency_channel[ii]   = { 
                                        'svn':              svn,
                                        'valid_from':       valid_from,
                                        'valid_to':         valid_to,
                                        'channel':          channel,
                                        'comment':          comment }

              satellite_mass[ii]                = { 
                                        'svn':              svn,
                                        'valid_from':       valid_from,
                                        'valid_to':         valid_to,
                                        'mass':             mass,
                                        'comment':          comment }

              satellite_com[ii]                 = { 
                                        'svn':              svn,
                                        'valid_from':       valid_from,
                                        'valid_to':         valid_to,
                                        'x':                x,
                                        'y':                y,
                                        'z':                z,
                                        'comment':          comment }
            
              satellite_eccentricity        = { 
                                        'svn':              svn,
                                        'equipment':        equipment,
                                        'type':             type,
                                        'x':                x,
                                        'y':                y,
                                        'z':                z,
                                        'comment':          comment }

              satellite_tx_power[ii]            = { 
                                        'svn':              svn,
                                        'valid_from':       valid_from,
                                        'valid_to':         valid_to,
                                        'power':            power,
                                        'comment':          comment }

           The counter 'ii' ranges from 0 to n and depends on how many plane, prn,
           frequency channel, mass, com and tx power changes have affected each satellite. If the time is defined as
           0000:000:00000 in the SINEX file, then the value is saved as 'None' in the Sinex class.

    """

    def setup_parser(self):
        return (
            self.file_reference,
            self.file_comment,
            self.satellite_identifier,
            self.satellite_plane,
            self.satellite_prn,
            self.satellite_frequency_channel,
            self.satellite_mass,
            self.satellite_com,
            self.satellite_eccentricity,
            self.satellite_tx_power,
        )

    #
    # Overwrite SINEX class methods
    #     
    def parse_file_reference(self, data: np.ndarray) -> None:
        """Parser for FILE/REFERENCE data
         
        Args:
            data (numpy.array):  Input data, raw data for FILE/REFERENCE block.
        """
        self.data.setdefault("file_reference", dict())
        for d in data:
            self.data["file_reference"].update({d[0].split()[0].lower(): str(d[1])})
    
    #
    # SINEX BLOCK
    #
    def parse_satellite_identifier(self, data):
        """Parse SATELLITE/IDENTIFIER SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_identifier")

    def parse_satellite_plane(self, data):
        """Parse SATELLITE/PLANE SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_plane")

    def parse_satellite_prn(self, data):
        """Parse SATELLITE/PRN SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_prn")

    def parse_satellite_frequency_channel(self, data):
        """Parse SATELLITE/FREQUENCY_CHANNEL SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_frequency_channel")

    def parse_satellite_mass(self, data):
        """Parse SATELLITE/MASS SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_mass")

    def parse_satellite_com(self, data):
        """Parse SATELLITE/COM SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_com")

    def parse_satellite_eccentricity(self, data):
        """Parse SATELLITE/ECCENTRICITY SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_eccentricity")

    def parse_satellite_tx_power(self, data):
        """Parse SATELLITE/TX_POWER SINEX block"""
        self._parse_sinex_block_lines(data, "satellite_tx_power")
        
    #
    # AUXILIARY FUNCTIONS
    #  
    def _parse_sinex_block_lines(self, data: np.ndarray, sinex_block_key: str) -> None:
        """Parse lines and save data related to given SINEX block key in self.data 
        
        Args:
            data:              Parsed data
            sinex_block_key:   SINEX block key (e.g. identifier, plane, ...)
        """
        valid_from_flag = False  # Needed to distinguish between different SINEX block formats with and without time period
        
        for d in data:
            satellite_key = str(d["svn"])
            self.data.setdefault(satellite_key, dict())
            self.data[satellite_key].setdefault(sinex_block_key, list())

            # Convert numpy data types to standard data types
            values = dict()
            for n in d.dtype.names:
                if n == "svn":    
                    continue
                if n == "valid_from":
                    valid_from_flag = True
                values[n] = d[n].item() if isinstance(d[n], np.generic) else d[n]  # Handling of None values

            if valid_from_flag:
                self.data[satellite_key][sinex_block_key].append(values)
            else:
                self.data[satellite_key][sinex_block_key] = values
