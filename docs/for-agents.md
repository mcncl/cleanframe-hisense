# Working with a coding agent

This project assumes a local agent that can access the user's computer or Docker host and home network. Reading the repository in a hosted chat does not provide TV access.

## For a user installation

Read `AGENTS.md`, [TV evidence](tv-status.md), then the [setup guide](agent-tv-setup-guide.md). Use the guide as the command sequence and [adapter reference](hisense.md) for API calls.

Before device work, establish:

| Detail | How to resolve it |
| --- | --- |
| Model, TV operating system and firmware | Ask the owner or inspect the TV's own About screen. A streaming stick's system is separate. Proceed with this implementation only for VIDAA. |
| Docker host and access | Reuse the owner's authorised connection and actual Compose project. Record its working directory, service and data paths privately. |
| TV address and server URL | Check both separately. The TV must reach the server URL; the server must reach the TV. |
| Pairing state | Preserve existing working state. For a new setup, prepare the pinned, checksum-verified connection file before requesting a PIN. |
| Apps and appearance | Ask what the owner wants. Discover real installed targets instead of copying another TV's IDs. |

When installation is already authorised, continue through the necessary setup steps; do not ask for confirmation before every reversible command. Announce launches/restarts and have the owner confirm visible results. Pause for genuinely missing access, a failed prerequisite or a required PIN, rather than guessing or bypassing a check.

Follow these stages in order:

1. Prepare paths, private environment and pairing file. Validate Compose configuration and file ownership.
2. Pair with the owner-present PIN, then start the service. Use fresh app discovery to verify connectivity.
3. Install the stable `cleanframehome` tile once. An unconfirmed API result requires a physical tile check before another install.
4. Verify the actual TV page, navigation and chosen native apps. Use the TV's Home editor to pin apps; server discovery alone does not change Home order.
5. Enable Home return only after the launcher works, and test it with the Hisense remote, including a quick repeat. Explain the off switch.
6. Leave a private setup record with paths, configuration, backup/recovery steps and visible passes/failures/unknowns. Give the owner their management URL and a short handoff.

## Using the running service

Use the protected HTTP actions for installation, opening, app refresh and navigation. Do not run `server.py install`, `open`, `status` or another paired client alongside the running service: a second connection with the same saved identity can interrupt it. Pair/re-pair only while that identity's other client is stopped.

Read fresh `runtime.location` after each navigation key and require CleanFrame to be foreground. `runtime.preferences` is a read-only snapshot of the TV's appearance and Home menu; it can seed a browser preview without changing the TV. Do not infer those settings from a fresh desktop browser's defaults.

A sent command, healthy container, saved session file or active-app report is not proof of the visible destination. Record owner confirmation separately from network observations. Do not claim screenshots or direct TV pixel access from focus/state reports. Keep power-on, Art Gallery and restart checks separate from Home return.

## Boundaries and privacy

Keep PINs, pairing tokens, certificate contents, control keys, photos, addresses and SSH details out of source and shared logs. Use ignored `.local/` or a private deployment directory. Do not copy the maintainer's private state into a new installation.

This project does not flash firmware, assign native startup settings, or install Android APKs. Preserve the TV's existing settings, tile identity and URL on upgrades. Use the documented stop/off route for recovery. Repository publication and protection changes require the owner's instruction.

## For browser contributions

```text
Read AGENTS.md and the development/interaction docs.
Make this change: <describe it>.
Preserve remote navigation, preference migrations and ES5 compatibility.
Use bundled public fonts and run the relevant isolated checks.
This task is browser-only; do not connect to or launch anything on my TV.
```

Read [development](development.md) and [testing](testing.md) for the isolated preview and test commands. Keep CleanFrame, Sidee and asset notices intact.
