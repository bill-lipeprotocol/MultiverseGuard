# Security

## Secret Handling

No API keys should be committed to this repository.

Use:

- local environment variables for development
- Streamlit Cloud secrets for hosted deployment
- `.env` locally only if ignored by Git

Never commit:

- `.env`
- `.streamlit/secrets.toml`
- screenshots containing keys
- provider dashboard screenshots
- terminal history containing keys

## Public Demo Safety

The app is intended for judge review and hackathon demonstration. Runtime secrets are configured server-side through Streamlit Cloud.

If `APP_ACCESS_CODE` is configured, live Cerebras/Together calls require that code. The app never logs or displays the access code or any API key.

## Secret Scan Commands

PowerShell (working tree):

```powershell
Get-ChildItem -Recurse -File |
  Where-Object {
    $_.FullName -notmatch "\\.git\\|\\.venv\\|__pycache__|\\.pytest_cache\\" -and
    $_.Name -ne ".env"
  } |
  Select-String -Pattern "csk-|tgp_|TOGETHER_API_KEY=|CEREBRAS_API_KEY="
```

Acceptable findings:

- `.env.example` placeholder lines
- README / doc placeholder lines
- test assertions checking that keys are absent

Unacceptable findings:

- a real Cerebras key
- a real Together key
- `.env` committed
- `.streamlit/secrets.toml` committed

Git history scan:

```powershell
git --no-pager log -p --all -S"csk-"
git --no-pager log -p --all -S"TOGETHER_API_KEY"
git --no-pager log -p --all -S"CEREBRAS_API_KEY"
```

Staged diff scan before commit:

```powershell
git --no-pager diff --cached | Select-String -Pattern "csk-|tgp_"
```

Expected: no output.
