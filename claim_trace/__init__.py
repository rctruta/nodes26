"""Trace one fabricated claim through graph-backed agent memory."""
import os

from claim_trace.constants import DISPLAY_ENV_DEFAULTS

# Applied at package import so the settings exist before any model library loads.
for _key, _value in DISPLAY_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
