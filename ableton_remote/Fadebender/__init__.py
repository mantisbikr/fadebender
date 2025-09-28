"""
Ableton Live Remote Script entry package for Fadebender.

Place this folder inside Ableton Live's MIDI Remote Scripts directory as:
  MIDI Remote Scripts/Fadebender/

Live will import this package and call create_instance(c_instance).
"""

from .Fadebender import create_instance  # noqa: F401

