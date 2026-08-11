# Versioning and releases

The project uses semantic versioning `MAJOR.MINOR.PATCH`:

- **MAJOR**: an incompatible change, including a new Home Assistant domain;
- **MINOR**: a new backward-compatible feature;
- **PATCH**: a backward-compatible fix without a major new feature.

Git tags are prefixed with `v`, for example `v1.0.1`. The value without the prefix must exactly match the `version` field in `custom_components/tsun_local/manifest.json`.

## Publishing a version

1. Update the version in `manifest.json`.
2. Add the version and its date to `CHANGELOG.md`.
3. Have the pull request reviewed and merged into `main`.
4. Create and push the corresponding tag:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v1.1.3 -m "Version 1.1.3"
   git push origin v1.1.3
   ```

5. The `release.yml` workflow automatically verifies that the tag, manifest, and changelog match, then creates the GitHub Release used by HACS.

Never move or reuse an already published tag. Any subsequent fix must receive a new version number.
