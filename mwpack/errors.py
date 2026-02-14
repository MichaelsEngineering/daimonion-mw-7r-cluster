"""Exit codes and domain errors for mwpack CLI."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    VALIDATION_ERROR = 2
    INTERNAL_ERROR = 3
    RENDERER_MISSING = 4


class MWPackError(Exception):
    exit_code = ExitCode.INTERNAL_ERROR


class ValidationError(MWPackError):
    exit_code = ExitCode.VALIDATION_ERROR


class RendererMissingError(MWPackError):
    exit_code = ExitCode.RENDERER_MISSING
