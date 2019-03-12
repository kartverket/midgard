"""A parser for reading Anubis xtr-files
"""

# Standard library imports
from collections import Counter
import itertools
import re
from typing import Type

# Midgard imports
from midgard.dev import exceptions
from midgard.dev import plugins
from midgard import parsers


@plugins.register
class AnubisXtrParser(parsers.Parser):
    """A parser for reading Anubis XTR files

    """

    def read_data(self) -> None:
        """Read data and store in .data dictionary
        """
        # Open file and read lines
        with self.file_path.open(encoding=self.file_encoding) as fid:
            header = next(fid)

            # Test header
            if not header.startswith("# G-Nut/Anubis"):
                warnings.warn(f"{self.file_path} is not an Anubis file")
                self.data_available = False
                return

            self.meta["version"] = header.split()[2].strip("[]")

            # Read file
            for line in fid:
                if line.startswith("#======"):
                    part = line.strip()[8:]
                    part_key = part.split()[0].lower()
                    self.data[part_key] = dict(__info__=dict(full_name=part))
                    section_data = self.data[part_key]
                    col_slices = None

                elif line.startswith("#"):
                    section = line[1:7].strip()
                    date = line[8:27]
                    section_data = self.data[part_key].setdefault(section, dict())

                    # Find column indices
                    start, end = itertools.tee(re.finditer(r"\S\s", line), 2)
                    next(end)
                    col_slices = [slice(s.end() - 1, e.end() - 1) for s, e in zip(start, end)][2:]
                    col_names = [line[s].strip().strip("_") for s in col_slices]

                    # Make sure column names are unique
                    for name, count in Counter(col_names).most_common():
                        if count == 1:
                            break
                        counter = 1
                        for idx, n in enumerate(col_names):
                            if n == name:
                                col_names[idx] = f"{name}_{counter}"
                                counter += 1

                elif line.startswith("="):
                    key = line[1:7].strip()
                    date = line[8:27]
                    if col_slices is None:
                        col_strings = line[28:].split()
                    else:
                        col_strings = [line[s].strip() for s in col_slices]

                    # Convert all things that look like numbers to numbers
                    col_values = list()
                    for s in col_strings:
                        try:
                            col_values.append(float(s))
                        except ValueError:
                            col_values.append(s)

                    section_data[key] = dict(zip(col_names, col_values)) if col_slices else dict(values=col_values)
                    section_data[key]["date"] = date
