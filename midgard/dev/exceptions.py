"""Definition of Midgard-specific exceptions

Description:
------------

Custom exceptions used by Midgard for more specific error messages and handling.

"""


class MidgardException(Exception):
    pass


class MidgardExit(SystemExit, MidgardException):
    pass


class InitializationError(MidgardException):
    pass


class FieldExistsError(MidgardException):
    pass


class FieldDoesNotExistError(MidgardException):
    pass


class MissingConfigurationError(MidgardException):
    pass


class MissingDataError(MidgardException):
    pass


class MissingEntryError(MidgardException):
    pass


class MissingSectionError(MidgardException):
    pass


class ParserError(MidgardException):
    pass


class TimerNotRunning(MidgardException):
    pass


class TimerRunning(MidgardException):
    pass


class UnknownConstantError(MidgardException):
    pass


class UnknownConversionError(MidgardException):
    pass


class UnknownEnumError(MidgardException):
    pass


class UnknownPackageError(MidgardException):
    pass


class UnknownPluginError(MidgardException):
    pass


class UnknownSystemError(MidgardException):
    pass


class UnitError(MidgardException):
    pass
