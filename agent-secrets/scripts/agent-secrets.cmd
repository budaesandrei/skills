@echo off
where uv >nul 2>nul
if errorlevel 1 (
  echo agent-secrets: uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/ 1>&2
  exit /b 127
)
if "%AGENT_SECRETS_VENV%"=="" set "AGENT_SECRETS_VENV=%USERPROFILE%\.agent-secrets\venv"
set "UV_PROJECT_ENVIRONMENT=%AGENT_SECRETS_VENV%"
uv run --quiet --project "%~dp0." --python 3.12 python "%~dp0agent_secrets.py" %*
