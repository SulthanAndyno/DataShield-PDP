"""
Audit logging and catalog persistence package
"""

from src.audit.audit_logger import (
    init_metadata_db,
    log_access_event,
    save_catalog_entry,
    get_pii_catalog,
    get_audit_logs,
)

__all__ = [
    "init_metadata_db",
    "log_access_event",
    "save_catalog_entry",
    "get_pii_catalog",
    "get_audit_logs",
]
