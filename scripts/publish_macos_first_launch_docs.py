#!/usr/bin/env python3
"""Compatibility wrapper for the public diagnostic documentation check.

Native macOS packages are no longer part of the official public distribution.
Keep this historical entry point so old automation or local commands fail safely
through the current documentation verifier instead of rewriting public pages.
"""

from sync_diagnostic_docs import main


if __name__ == "__main__":
    main()
