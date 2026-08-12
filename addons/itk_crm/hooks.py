"""Hooks for itk_crm — Neuinstallation: ITK-CRM-Struktur herstellen.

Hinweis: post_init_hook wird von Odoo 18 NUR bei Neuinstallation ausgefuehrt.
Fuer Upgrades/Restores sorgt die Post-Migration (migrations/18.0.1.3.0/).
"""
import logging

from . import setup_runtime

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Neuinstallation: idempotentes Struktur-Setup (Stages, Menüs, Felder, ...)."""
    _logger.info("itk_crm post_init_hook: Struktur-Setup (Neuinstallation)")
    setup_runtime.setup_all(env)
