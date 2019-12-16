import logging
from discreetly.session import Session  # noqa: F401
from pkg_resources import get_distribution, DistributionNotFound

logging.getLogger(__name__).addHandler(logging.NullHandler())

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
