# Working with a coding agent

Read `AGENTS.md`, development and interaction behaviour first. Browser work and TV work have different effects. A hosted agent cannot access the TV simply by reading this repository.

For interface work:

```text
Read AGENTS.md and the development/interaction docs.
Make this change: <describe it>.
Preserve remote navigation, preference migrations and ES5 compatibility.
Use the bundled public fonts and run the relevant isolated checks.
This task is browser-only; do not connect to or launch anything on my TV.
```

For a TV installation, obtain the model, VIDAA/firmware version, server runtime, addresses and desired apps. Read `docs/agent-tv-setup-guide.md`. Confirm the client bundle exists locally before starting PIN pairing. Keep the PIN, session, client bundle, control key and addresses out of source and shared output.

Use the running service for installation/launch API calls; do not open a competing MQTT connection with its identity. Preserve `cleanframehome` on an existing installation. Announce launches and service restarts. Ask the owner to verify real rendering, app destinations, Home return and native Art Gallery behaviour. Save private details in `.local/`; record only model/firmware and observed results in shared compatibility notes.

This project does not flash firmware or assign native startup settings. Home return is an optional service setting with a reversible off switch. Repository publication or a visibility change requires the owner's instruction. Retain CleanFrame and Sidee attribution and third-party asset notices.
