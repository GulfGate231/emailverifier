# Email Verifier Pro

A powerful, self-hosted email verification tool built in Python with Streamlit GUI. Verify thousands/millions of emails for syntax, domain activity, disposable/role/free providers, and deep mailbox existence (SMTP probe) — **without sending any actual emails**.

Multiple versions included for different needs: from basic to ultra-fast optimized.

**Features**:
- Syntax validation
- MX record check
- Disposable, role-based, free/personal provider detection
- Deep SMTP verification (mailbox exists & deliverable)
- Typo suggestions (in some versions)
- Deduplication
- CSV/TXT input → CSV output
- Web GUI with progress bar and direct downloads

**All versions are self-hosted — no API keys needed except the DeBounce version.**

## Versions Included

| File | Description | Best For | Speed Level |
|------|-------------|----------|-------------|
| `email_verifier_ultimate.py` | Full-featured CLI version with logging, CSV output, role/disposable/free detection | Scripted/batch runs on server | Medium |
| `email_verifier_gui.py` | Basic Streamlit GUI version | Interactive use | Medium |
| `email_verifier_gui_fast.py` | Optimized GUI: domain caching, early skips | Faster self-hosted verification | Fast |
| `email_verifier_gui_max.py` | **MAX SPEED** — aggressive caching, skips SMTP for free providers, 1 MX try, low timeout, high threads | Largest lists, fastest possible self-hosted | **Ultra Fast** (recommended) |
| `email_verifier_debounce_gui.py` | Uses your DeBounce API key — professional speed & accuracy | When you want ZeroBounce/DeBounce-level results | Lightning Fast (paid) |

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/GulfGate231/emailverifier.git
cd emailverifier



**You need Python 3.8+ and these packages:**
python3 -m venv emailverifier_env
source emailverifier_env/bin/activate
pip install streamlit pandas requests dnspython
