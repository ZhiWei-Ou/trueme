"""Failures translated into stable CLI exit codes."""


class TrueMeError(Exception):
    exit_code = 5


class InputError(TrueMeError):
    exit_code = 2


class ModelError(TrueMeError):
    exit_code = 3


class DeviceError(TrueMeError):
    exit_code = 4


class ProcessingError(TrueMeError):
    exit_code = 5


class ReportError(TrueMeError):
    exit_code = 6
