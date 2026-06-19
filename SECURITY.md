# Security policy

## Supported version

Only the latest commit on `main` is supported while this portfolio project is pre-1.0.

## Report a vulnerability

Open a private GitHub security advisory when the repository is published. Do not put API keys,
source documents, provider responses, or other sensitive data in a public issue.

## Credential handling

- Users enter keys into a masked Streamlit field for the active session.
- The app passes a key only to the selected provider SDK and does not log or persist it.
- `.env`, `.streamlit/secrets.toml`, output files, and temporary files are ignored by Git.
- CI never needs live provider credentials because provider clients are replaced in tests.

If a key is pasted into a commit, issue, chat, log, or screenshot, revoke it immediately in the
provider console and create a replacement. Removing the text later is not sufficient because the
credential may already have been copied or retained in history.

## Deployment checklist

- Keep `main` protected and require the test workflow before merge.
- Enable GitHub secret scanning and push protection where available.
- Do not place provider keys in Streamlit Community Cloud secrets for this bring-your-own-key app.
- Review dependency updates and model deprecations regularly.
- Re-test provider authentication errors to ensure SDK details are not reflected to users.
