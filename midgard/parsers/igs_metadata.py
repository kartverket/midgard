# Standard library imports
from typing import Any, Dict, Iterable

# Midgard imports
from midgard.dev import plugins
from midgard.parsers import ChainParser, ParserDef
import os




@plugins.register
class MetadataParser(ChainParser):
    def setup_parser(self) -> Iterable[ParserDef]:
        fileRefParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-FILE/REFERENCE"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseFile,
                    "fields": {
                        "contents": (0, None)
                    },  # Note that due to multiline comments and file references the contents is dumped into self.meta
                }
            },
        )
        fileCommentParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-FILE/COMMENT"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseComment,
                    "fields": {
                        "contents": (0, None)
                    },  # Note that due to multiline comments and file references the contents is dumped into self.meta
                }
            },
        )
        satIDParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/IDENTIFIER"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseID,
                    "fields": {
                        "SVN": (1, 6),
                        "COSPAR ID": (6, 16),
                        "SatCat": (16, 23),
                        "Block": (23, 39),
                        "Comment": (39, None),
                    },
                }
            },
        )

        satPlaneParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/PLANE"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parsePlane,
                    "fields": {
                        "SVN": (1, 6),
                        "ValidFrom": (6, 21),
                        "ValidTo": (21, 36),
                        "P": (36, 38),
                        "Slot": (38, 45),
                        "comment": (45, None),
                    },
                },
            },
        )
        satPRNParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/PRN"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parsePRN,
                    "fields": {
                        "SVN": (1, 6),
                        "ValidFrom": (6, 21),
                        "ValidTo": (21, 36),
                        "PRN": (36, 40),
                        "comment": (40, None),
                    },
                },
            },
        )

        satFreqChanParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/FREQUENCY_CHANNEL"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseFreqChan,
                    "fields": {
                        "SVN": (1, 6),
                        "ValidFrom": (6, 21),
                        "ValidTo": (21, 36),
                        "Channel": (36, 40),
                        "comment": (40, None),
                    },
                },
            },
        )

        satMassParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/MASS"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseMass,
                    "fields": {
                        "SVN": (1, 6),
                        "ValidFrom": (6, 21),
                        "ValidTo": (21, 36),
                        "Mass": (36, 46),
                        "comment": (46, None),
                    },
                },
            },
        )

        satCoMParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/COM"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseCOM,
                    "fields": {
                        "SVN": (1, 6),
                        "ValidFrom": (6, 21),
                        "ValidTo": (21, 36),
                        "X": (36, 46),
                        "Y": (46, 56),
                        "Z": (56, 66),
                        "comment": (66, None),
                    },
                },
            },
        )

        satEccentricityParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/ECCENTRICITY"),
            label=lambda _line, _: True,
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseEccentricity,
                    "fields": {
                        "SVN": (1, 6),
                        "Equipment": (6, 27),
                        "T": (27, 29),
                        "X": (29, 39),
                        "Y": (39, 49),
                        "Z": (49, 59),
                        "comment": (59, None),
                    },
                },
            },
        )
        satTxPowerParser = ParserDef(
            end_marker=lambda line, _ln, _: line.startswith("-SATELLITE/TX_POWER"),
            label=lambda _line, _: "",
            skip_line=lambda line: line.strip().startswith(("*", "%", "+", "-")),
            parser_def={
                True: {
                    "parser": self._parseTxPower,
                    "fields": {
                        "SVN": (1, 6),
                        "ValidFrom": (6, 21),
                        "ValidTo": (21, 36),
                        "Power": (36, 41),
                        "comment": (41, None),
                    },
                },
            },
        )

        parselist = [
            fileRefParser,
            fileCommentParser,
            satIDParser,
            satPlaneParser,
            satPRNParser,
            satFreqChanParser,
            satMassParser,
            satCoMParser,
            satEccentricityParser,
            satTxPowerParser,
        ]

        return parselist

    def _parseFile(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        self.meta.setdefault("File Reference", []).append(line["contents"])

    def _parseComment(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        self.meta.setdefault("File Comment", []).append(line["contents"])

    def _parsePRN(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["ValidFrom"]
        self.data.setdefault(line["SVN"], {}).setdefault("prn", {})[line["ValidFrom"]] = temp

    def _parseID(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        self.data.setdefault(line["SVN"], {})["ID"] = temp

    def _parsePlane(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["ValidFrom"]
        self.data.setdefault(line["SVN"], {}).setdefault("plane", {})[line["ValidFrom"]] = temp

    def _parseMass(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["ValidFrom"]
        self.data.setdefault(line["SVN"], {}).setdefault("mass", {})[line["ValidFrom"]] = temp

    def _parseFreqChan(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["ValidFrom"]
        self.data.setdefault(line["SVN"], {}).setdefault("frequency channel", {})[line["ValidFrom"]] = temp

    def _parseCOM(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["ValidFrom"]
        self.data.setdefault(line["SVN"], {}).setdefault("COM", {})[line["ValidFrom"]] = temp

    def _parseTxPower(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["ValidFrom"]
        self.data.setdefault(line["SVN"], {}).setdefault("Tx Power", {})[line["ValidFrom"]] = temp

    def _parseEccentricity(self, line: Dict[str, str], _: Dict[str, Any]) -> None:
        temp = line.copy()
        del temp["SVN"]
        del temp["Equipment"]
        self.data.setdefault(line["SVN"], {}).setdefault(f"eccentricity", {})[line["Equipment"]] = temp
