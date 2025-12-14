```
🚀🚀 **Ultimate Self-Hosted Email Verifier Pro** 🚀🚀

Verify thousands (even millions) of emails for FREE on your own VPS or laptop!

Features:
• Syntax + domain validation
• MX record check
• Detects disposable, role-based (info@, admin@), and free providers (Gmail, Yahoo, etc.)
• Deep SMTP probe — confirms mailbox actually exists & can receive email (no actual email sent)
• Deduplication, typo suggestions (some versions)
• Beautiful Streamlit web GUI with live progress bar
• Direct download of valid & invalid CSV files

Fully open-source, private, no third-party API needed (except DeBounce version if you have an account).

👉 **GitHub Repository**: https://github.com/GulfGate231/emailverifier.git

──────────────────────────────────
Included Versions
──────────────────────────────────

• email_verifier_ultimate.py → Full CLI version with logging
• email_verifier_gui.py → Basic GUI
• email_verifier_gui_fast.py → Faster with domain caching
• email_verifier_gui_max.py → MAX SPEED (aggressive optimizations — recommended for large lists)
• email_verifier_debounce_gui.py → Uses DeBounce API (lightning fast + pro accuracy)

──────────────────────────────────
Requirements
──────────────────────────────────

1. Install Git (needed for git clone)
   • Windows: https://git-scm.com/download/win (choose "Git from command line" during install)
   • Linux/VPS: Usually pre-installed or `sudo apt install git`

2. Install Python 3.8+
   • Windows: https://www.python.org/downloads/ → Check "Add Python to PATH"
   • Linux/VPS: Usually pre-installed

3. Python packages:
   pip install streamlit pandas requests dnspython

──────────────────────────────────
📥 How to Install & Run
──────────────────────────────────

1. Get the project
Open terminal (Linux/VPS) or PowerShell/Command Prompt (Windows):

git clone https://github.com/GulfGate231/emailverifier.git
cd emailverifier

(Alternative: No Git? Go to GitHub → green Code button → Download ZIP → extract)

2. Install packages
pip install streamlit pandas requests dnspython

──────────────────────────────────
Option A: On VPS (Ubuntu/Linux) – Best for Large Lists
──────────────────────────────────

1. SSH into your VPS
2. Clone + install as above
3. (Recommended) Virtual environment:
```bash
python3 -m venv verifier_env
source verifier_env/bin/activate
pip install streamlit pandas requests dnspython
```

4. Run any version (add --server.address=0.0.0.0 for remote access):
```bash
# Max speed (recommended)
streamlit run email_verifier_gui_max.py --server.port=8501 --server.address=0.0.0.0

# Fast version
streamlit run email_verifier_gui_fast.py --server.port=8501 --server.address=0.0.0.0

# Basic GUI
streamlit run email_verifier_gui.py --server.port=8501 --server.address=0.0.0.0

# DeBounce version (needs API key)
streamlit run email_verifier_debounce_gui.py --server.port=8501 --server.address=0.0.0.0

# CLI version (no GUI)
python email_verifier_ultimate.py
```

5. Allow port:
```bash
sudo ufw allow 8501
```

6. Open: http://YOUR_VPS_IP:8501 → set threads to 40-50

──────────────────────────────────
Option B: On Windows Laptop – Great for Testing
──────────────────────────────────

1. Install Git + Python (links above)
2. Clone + install packages as above
3. Run any version:
```powershell
# Max speed (recommended)
streamlit run email_verifier_gui_max.py

# Fast version
streamlit run email_verifier_gui_fast.py

# Basic GUI
streamlit run email_verifier_gui.py

# DeBounce version
streamlit run email_verifier_debounce_gui.py

# CLI version
python email_verifier_ultimate.py
```

→ Opens at http://localhost:8501 (press Enter if welcome email prompt appears)

──────────────────────────────────
How to Run Multiple Verifiers (Different Ports)
──────────────────────────────────

Open a new terminal/PowerShell window for each:

```bash
# Instance 1
streamlit run email_verifier_gui_max.py --server.port=8501

# Instance 2
streamlit run email_verifier_gui_fast.py --server.port=8502

# Instance 3
streamlit run email_verifier_gui.py --server.port=8503
```

On VPS, add --server.address=0.0.0.0

Open in browser:
• http://localhost:8501 (or YOUR_VPS_IP:8501)
• http://localhost:8502
• http://localhost:8503
etc.

──────────────────────────────────
How to Use
──────────────────────────────────

• Upload .txt (one email per line) or .csv (email in first column)
• Adjust threads (higher = faster, 40-50 on VPS)
• Click Start → download valid/invalid CSVs when done

Pro Tips:
• For 500k+ emails → use email_verifier_gui_max.py with 50 threads (expect 3-8 hours)
• Run overnight on VPS
• Responsible use only — verify your own/opt-in lists!

Star the repo ⭐ Questions? Comment here!

Built by @hustl3andbustl3 / GulfGate231
Enjoy the power! 🔥
```
