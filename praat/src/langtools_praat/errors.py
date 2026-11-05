"""Errors safe to present in either a CLI or desktop dialog."""


class InvalidInput(ValueError):
    """Invalid content, parameter, geometry, or unsupported input."""


class StaleRevision(InvalidInput):
    """The operation was based on an obsolete document revision."""


class Cancelled(Exception):
    """A caller cancelled a bounded operation."""
