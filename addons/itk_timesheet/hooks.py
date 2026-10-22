"""itk_timesheet: Hook fuer die Neuinstallation."""
import logging

from . import setup_runtime

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Neuinstallation: Menue-Wortlaute in Quelle + de_DE + en_US setzen."""
    _logger.info("itk_timesheet post_init_hook: Wortlaute setzen")
    setup_runtime.setup_all(env)
