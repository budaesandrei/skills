---
name: agent-secrets
description: Securely store and use secrets (API keys, tokens, passwords, certificates, JSON credentials) in the operating system's keyring through a local input window. Works on macOS, Windows and Linux desktops. Use whenever the user says they have a secret, key, token, password or credential to store, or when a task needs a secret that was stored earlier. Never accept a secret in chat.
---

# agent-secrets

Secrets go from a local window straight into the system keyring (macOS Keychain, Windows Credential Manager, or Secret Service on Linux). You only ever see metadata.

Run the launcher from this skill's `scripts` folder: `scripts/agent-secrets` on macOS and Linux, `scripts\agent-secrets.cmd` on Windows. Examples below write `agent-secrets` for either.

## First use on a machine

1. If `uv` is missing, ask the user before installing it from https://docs.astral.sh/uv/getting-started/installation/
2. Run `agent-secrets doctor`. The first run builds the environment and can take a minute. If `ready` is false, tell the user the `reason`. This skill needs a machine with a screen and a system keyring, so it can't run in a cloud sandbox or on a headless server.
3. For Claude Desktop chat, run `agent-secrets connect-desktop`, then ask the user to restart Claude Desktop.

## Rules

- Never ask for, accept, print, log or write a secret value. If one is pasted into chat, do not repeat or store it. Tell the user it is exposed and should be rotated, then open the window.
- Never pass a secret value in `--prefill`.
- Never read a value directly from the keyring or with tools like `keyring get` or `security find-generic-password -w`. Use `exec`.
- Never run a command through `exec` that would print the variable, such as `env`, `printenv` or `echo $VAR`.
- Confirm with the user before `delete` or before replacing a `prd` secret.

## Store a secret

1. Prefill everything you can infer from the conversation. Leave out what you don't know. Don't guess an expiry.
2. Run this in the background if your tool supports it, so you are notified when the window closes. Otherwise wait up to 10 minutes for it to finish.

```bash
agent-secrets prompt --prefill '{"name":"openai-api-key","type":"api_token","env":"dev","provider":"OpenAI","description":"Used by the reporting script","env_var":"OPENAI_API_KEY"}'
```

3. Tell the user the window is open. The result arrives as JSON on stdout:
   - `stored`: exit 0, with `secret` holding the metadata and access details.
   - `cancelled` or `timeout`: exit 3. Nothing was stored. The window closes itself after 10 minutes.
   - `unavailable`: exit 4, with a `reason`. Nothing was stored.
4. On `stored`, confirm the name and environment, and save a short memory if memory is available: name, env, type, purpose, expiry, and the `exec` line. Never the value.

Prefill fields: `name` (letters, numbers, `.`, `_`, `-`), `type`, `env`, `description`, `provider`, `expires` (YYYY-MM-DD), `never_expires`, `env_var`, `username`, `url`, `project`, `owner`, `rotate_days`, `tags`, `scopes`, `notes`.

Types: `api_token`, `password`, `bearer_token`, `oauth_client_secret`, `oauth_refresh_token`, `webhook_secret`, `connection_string`, `encryption_key`, `totp_seed`, `ssh_private_key`, `private_key`, `certificate`, `json`, `env_file`, `recovery_codes`, `other`.

Environments: `none`, `local`, `dev`, `stg`, `prd`.

## Use a secret

```bash
agent-secrets list                 # metadata and expiry warnings
agent-secrets exec --map openai-api-key@dev -- python report.py
agent-secrets exec --map TOKEN=stripe@prd -- ./deploy.sh
agent-secrets delete openai-api-key@dev
```

`--map` can repeat. `VAR=` is optional when the secret has a stored environment variable. `@env` is required when a name exists in more than one environment.

When an app has to be given a secret by hand, run `agent-secrets copy NAME@ENV` in the background only once the person says they are at the field. It holds the value on the clipboard for 45 seconds, then clears it. Never read the clipboard while it runs.

Without a shell (Claude Desktop chat), use the `secret_prompt`, `secret_prompt_status` and `secret_list` connector tools. Call `secret_prompt_status` until the status is not `pending`. Those tools cannot read values.

Metadata is kept in `~/.agent-secrets/registry.json`. Values are never written there.
