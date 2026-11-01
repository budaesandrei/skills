"""Claude Desktop connector for agent-secrets. Exposes metadata only.

There is deliberately no tool that returns a secret value.
"""
import json
import time

from mcp.server.mcpserver import MCPServer

import agent_secrets as core

server = MCPServer("agent-secrets")


@server.tool()
def secret_prompt(
    name: str = "",
    type: str = "",
    env: str = "",
    description: str = "",
    provider: str = "",
    expires: str = "",
    never_expires: bool = False,
    env_var: str = "",
    username: str = "",
    url: str = "",
    project: str = "",
    owner: str = "",
    rotate_days: int = 0,
    tags: str = "",
    scopes: str = "",
    notes: str = "",
) -> str:
    """Open the local window where the person types a secret into the system keyring.

    Prefill any metadata known from the conversation. Never pass a secret value,
    and never ask the person to paste one into chat. Returns a request_id; call
    secret_prompt_status with it until the status is no longer "pending".
    type: api_token, password, bearer_token, oauth_client_secret, oauth_refresh_token,
    webhook_secret, connection_string, encryption_key, totp_seed, ssh_private_key,
    private_key, certificate, json, env_file, recovery_codes, other.
    env: none, local, dev, stg, prd. expires: YYYY-MM-DD.
    """
    prefill = {k: v for k, v in locals().items() if v}
    return json.dumps({"request_id": core.start_request(prefill), "status": "pending"})


@server.tool()
def secret_prompt_status(request_id: str, wait_seconds: int = 45) -> str:
    """Wait for the person to finish the secret window. Returns metadata, never the value.

    status: pending (call again), stored, cancelled or timeout.
    """
    deadline = time.monotonic() + min(max(wait_seconds, 0), 50)
    while True:
        res = core.read_request(request_id)
        if res is not None:
            return json.dumps(res)
        if time.monotonic() >= deadline:
            return json.dumps({"status": "pending"})
        time.sleep(0.5)


@server.tool()
def secret_list(env: str = "") -> str:
    """List stored secrets' metadata and how to reach them. Never returns values."""
    rows = list(core.load_registry().values())
    if env:
        rows = [r for r in rows if r["env"] == env]
    return json.dumps([{**core.public_ref(r), "warnings": core.warnings(r)} for r in rows])


if __name__ == "__main__":
    server.run()
