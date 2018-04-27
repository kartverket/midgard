"""Definition of Midgard-specific exceptions

Description:
------------

Custom exceptions used by Midgard for more specific error messages and handling.


Authors:
--------

* Geir Arne Hjelle <geir.arne.hjelle@kartverket.no>

$Revision: 14777 $
$Date: 2018-04-11 23:17:27 +0200 (Wed, 11 Apr 2018) $
$LastChangedBy: hjegei $

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


class MissingDataError(MidgardException):
    pass


class UnknownEnumError(MidgardException):
    pass


class UnknownPluginError(MidgardException):
    pass


class UnitError(MidgardException):
    pass
