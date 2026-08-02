# Releasing the macOS app

The `macOS App` GitHub Actions workflow builds a DMG. Manual workflow runs may produce an unsigned test artifact. Version tags only publish a release when all signing and notarization credentials are configured.

## Apple prerequisites

You need an active Apple Developer Program membership and a `Developer ID Application` certificate exported as a password-protected `.p12` file.

Add these GitHub Actions repository secrets:

| Secret | Value |
| --- | --- |
| `APPLE_CERTIFICATE_BASE64` | Base64-encoded `.p12` certificate (`base64 -i certificate.p12`) |
| `APPLE_CERTIFICATE_PASSWORD` | Password used when exporting the `.p12` |
| `APPLE_SIGNING_IDENTITY` | Full identity, such as `Developer ID Application: Name (TEAMID)` |
| `APPLE_ID` | Apple Account email used for notarization |
| `APPLE_TEAM_ID` | Apple Developer team ID |
| `APPLE_APP_PASSWORD` | App-specific password for the Apple Account |

## Test an unsigned build

Run the `macOS App` workflow manually from GitHub Actions, or build locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-build.txt
./scripts/build_macos.sh
open "dist/Concepts Mindmap Viewer.app"
```

## Publish a release

After the secrets are configured and the main branch is green:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow builds the app, verifies its signature, creates the DMG, submits it to Apple's notary service, staples the notarization ticket, and publishes it to GitHub Releases.
