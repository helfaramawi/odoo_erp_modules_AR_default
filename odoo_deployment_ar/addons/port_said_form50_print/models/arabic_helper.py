# -*- coding: utf-8 -*-
"""
Arabic text reshaping helper for wkhtmltopdf compatibility.
wkhtmltopdf does not support Arabic shaping natively.
This module pre-shapes Arabic text so it renders correctly in PDF.
"""
import logging
_logger = logging.getLogger(__name__)

def reshape_arabic(text):
    """Reshape Arabic text for correct wkhtmltopdf rendering."""
    if not text:
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception as e:
        _logger.warning("Arabic reshaping failed: %s", e)
        return text
