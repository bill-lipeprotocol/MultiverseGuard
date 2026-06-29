# Deployment

## Streamlit Community Cloud

Recommended settings:

- Repository: `bill-lipeprotocol/MultiverseGuard`
- Branch: `main`
- Main file path: `src/ui/app.py`
- Python version: `3.10`

## Secrets

Configure these in Streamlit Cloud secrets, not in GitHub:

```toml
CEREBRAS_API_KEY = "your_cerebras_key_here"
CEREBRAS_MODEL = "gemma-4-31b"
MULTIVERSEGUARD_MOCK = "false"

TOGETHER_API_KEY = "your_together_key_here"
TOGETHER_BASE_URL = "https://api.together.ai/v1"
TOGETHER_MODEL = "zai-org/GLM-5.2"

APP_ACCESS_CODE = "choose_a_demo_code"
```

> Never commit `.env` or `.streamlit/secrets.toml`. Both are git-ignored.

## Access Code Gate (Optional)

If `APP_ACCESS_CODE` is set, the hosted app requires that code before live Cerebras/Together calls. Mock mode, documentation, and the page itself remain visible without the code. If `APP_ACCESS_CODE` is not set, local development behaves normally with no gate.

## Local PowerShell Setup

```powershell
git clone https://github.com/bill-lipeprotocol/MultiverseGuard.git
cd MultiverseGuard

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:CEREBRAS_API_KEY="your_cerebras_key_here"
$env:CEREBRAS_MODEL="gemma-4-31b"
$env:MULTIVERSEGUARD_MOCK="false"

$env:TOGETHER_API_KEY="your_together_key_here"
$env:TOGETHER_BASE_URL="https://api.together.ai/v1"
$env:TOGETHER_MODEL="zai-org/GLM-5.2"

# Optional: gate live calls on a public deployment
$env:APP_ACCESS_CODE="choose_a_demo_code"

python -m streamlit run src/ui/app.py
```

## Verification

```powershell
python -m py_compile src\ui\app.py src\graph\multiverse_graph.py src\utils\cerebras_client.py src\utils\speed_benchmark.py
pytest -q
```

Expected: `36 passed`.
