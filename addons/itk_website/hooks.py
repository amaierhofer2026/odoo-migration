"""Installations-Hook: Struktur-Setup einmalig nach der Installation."""
import logging

from . import setup_runtime

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    _logger.info("itk_website: post_init_hook")
    setup_runtime.setup_all(env)
