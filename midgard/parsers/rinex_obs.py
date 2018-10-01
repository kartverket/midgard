"""A parser for reading Rinex observation files
"""

# Standard library imports
from typing import Type

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard import parsers


@plugins.register
class RinexObsParser(parsers.RinexParser):
    """A parser for reading Rinex observation files

    Different versions of the Rinex format are implemented as subclasses
    """

    def read_data(self) -> None:
        """Dispatch to correct subclass based on version in Rinex file

        Need to make sure the dispatch only happens for RinexObsParsers, not for subclasses.
        """
        if self.__class__.__name__ == "RinexObsParser":
            Parser: Type[parsers.RinexParser]

            # Find correct parser subclass
            version = self.get_rinex_version()
            if version.startswith("3"):
                from midgard.parsers.rinex3_obs import Rinex3ObsParser

                Parser = Rinex3ObsParser
            elif version.startswith("2"):
                from midgard.parsers.rinex2_obs import Rinex2ObsParser

                Parser = Rinex2ObsParser
            else:
                raise exceptions.ParserError(f"Unknown version {version!r} for Rinex observation files")

            # Read data with correct parser
            parser = Parser(**self.meta["__kwargs__"])
            parser.read_data()

            # Copy data to self
            self.header.update(parser.header)
            self.data.update(parser.data)

        else:
            super().read_data()
