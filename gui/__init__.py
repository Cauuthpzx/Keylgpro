#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI package for the Keylogger application
"""

__author__ = "Developer"
__version__ = "1.0.0"

from .resources import UIResources
from .app import ModernKeyloggerApp
from .frames import *

__all__ = ['UIResources', 'ModernKeyloggerApp', 'frames']