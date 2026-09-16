#!/usr/bin/env python3
"""Compatibility wrapper for the public diagnostic documentation check.

This historical helper no longer rewrites macOS copy because the supported public
cross-platform path is the full Python package. Keeping the entry point avoids
breaking old local commands while preventing stale native-package text from being
restored.
"""

from sync_diagnostic_docs import main


if __name__ == "__main__":
    main()
