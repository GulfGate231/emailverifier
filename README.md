🚀 **Ultimate Self-Hosted Email Verifier Pro** 🚀

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

Included versions:
• email_verifier_ultimate.py → Full CLI version with logging
• email_verifier_gui.py → Basic GUI
• email_verifier_gui_fast.py → Faster with caching
• email_verifier_gui_max.py → MAX SPEED (recommended for large lists)
• email_verifier_debounce_gui.py → Uses DeBounce API (lightning fast + pro accuracy)

──────────────────────────────────
📥 How to Install & Run
──────────────────────────────────

1. Clone the repository
Open terminal (Linux/VPS) or PowerShell/Command Prompt (Windows):

git clone https://github.com/GulfGate231/emailverifier.git
cd emailverifier

(Alternative: Download ZIP from GitHub → Code → Download ZIP → extract)

2. Install required packages

pip install streamlit pandas requests dnspython

──────────────────────────────────
Option A: Install on VPS (Ubuntu/Linux) – Best for large lists
──────────────────────────────────

1. SSH into your VPS
2. Run the clone commands above
3. (Recommended) Create a virtual environment:

python3 -m venv verifier_env
source verifier_env/bin/activate
pip install streamlit pandas requests dnspython

4. Run the fastest version (recommended):

streamlit run email_verifier_gui_max.py --server.port=8501 --server.address=0.0.0.0

5. Allow the port in firewall (if needed):

sudo ufw allow 8501

6. Open in your browser:
http://YOUR_VPS_IP:8501

→ Upload your list, set threads to 40-50, and start!

──────────────────────────────────
Option B: Install on Windows Laptop – Great for testing
──────────────────────────────────

1. Install Python from https://www.python.org/downloads/ 
   → IMPORTANT: Check "Add Python to PATH" during installation

2. Open PowerShell or Command Prompt as normal user

3. Run the clone commands above

4. Install packages:

pip install streamlit pandas requests dnspython

5. Run the fastest version:

streamlit run email_verifier_gui_max.py

→ It will automatically open in your browser at http://localhost:8501

──────────────────────────────────
How to Use (All Versions)
──────────────────────────────────

• Upload .txt file (one email per line) or .csv (email in first column)
• Adjust threads (higher = faster, 40-50 recommended on VPS)
• Click Start Verification
• Wait for progress bar → download valid_*.csv and invalid_*.csv when finished

Pro Tips:
• For 500k+ emails → use email_verifier_gui_max.py with 50 threads (expect 3-8 hours)
• Run overnight on VPS for huge lists
• Only verify your own or opt-in lists — responsible use only!

Star the repo if you like it ⭐
Questions? Drop them here!

Built by @Abundance
Enjoy the power! 🔥
