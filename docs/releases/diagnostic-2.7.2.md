# TSUN Local Diagnostic 2.7.2

Diagnostic 2.7.2 extends the full read-only capture with passive inspection of the logger network and firmware-update web interfaces.

## Read-only web-interface research

Full diagnostic mode now GETs a bounded set of local pages including `wireless.html`, `wizard.html`, `remote.html`, `update.html` and `invupdate.html`.

It records only passive interface metadata:

- form method and same-device action path;
- field names and field types, never field values;
- same-device script paths;
- JavaScript handler names referenced by HTML events;
- candidate same-device HTML/CGI endpoints found as quoted path literals.

The diagnostic does **not** submit forms, execute JavaScript, upload firmware, change DNS/network settings or reboot the logger.

## Windows updater

The Windows GUI is now **1.4.1**. The updater also compares the embedded `tsun_dump.py` version with the public diagnostic manifest. A newer dump engine can therefore refresh the portable EXE even when the GUI itself did not otherwise need a version change.

The GUI version bump from 1.4.0 to 1.4.1 also ensures already-downloaded 1.4.0 executables transition to the corrected updater.

## Safety and privacy

TSUN Local Diagnostic remains strictly local and read-only. DNS addresses, full inverter/logger serial numbers, full MAC addresses, credentials and form values are not stored.
