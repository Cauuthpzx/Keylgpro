#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Frames package for the GUI components
"""

__author__ = "Developer"
__version__ = "1.0.0"
# Thêm vào file gui/frames/__init__.py
from .screenshot_frame import ScreenshotFrame
from .keylogger_frame import KeyloggerFrame
from .management_frame import ManagementFrame
from .bait_frame import BaitFrame
from .cookie_frame import CookieFrame
from .settings_frame import SettingsFrame
from .about_frame import AboutFrame

__all__ = [
    'KeyloggerFrame',
    'ManagementFrame',
    'BaitFrame',
    'CookieFrame',
    'SettingsFrame',
    'AboutFrame'
]
