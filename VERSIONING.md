# Versioning and releases

The project follows Semantic Versioning using `MAJOR.MINOR.PATCH`:

- **MAJOR**: an incompatible change, such as changing the Home Assistant domain;
- **MINOR**: a backward-compatible feature;
- **PATCH**: a backward-compatible correction.

Git tags use a `v` prefix. For example, release `1.2.1` uses tag `v1.2.1`. The version without the prefix must match `version` in `custom_components/tsun_local/manifest.json`.

## Release checklist

1. Update the version in `custom_components/tsun_local/manifest.json`.
2. Add a matching version section and date to `CHANGELOG.md`.
3. Confirm that every README describes the same features and compatibility state.
4. Run the complete test suite and validate every JSON file.
5. Commit and merge the prepared changes into `main`.
6. Create and push the matching annotated tag:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v1.2.1 -m "Version 1.2.1"
   git push origin v1.2.1
   ```

7. The release workflow verifies that the tag, manifest, and changelog agree, then creates the GitHub Release used by HACS.

The workflow is idempotent: if a GitHub Release already exists for the tag, it exits successfully without trying to recreate it.

Never move or reuse a published tag. Every later correction must receive a new version number.
