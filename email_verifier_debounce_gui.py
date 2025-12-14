import streamlit as st
import pandas as pd
import re
import requests
import time
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, as_completed

# DeBounce API Config
DEBounce_API_KEY = st.sidebar.text_input("DeBounce API Key", type="password", help="Get from your DeBounce dashboard > API")
SINGLE_ENDPOINT = "https://api.debounce.io/v1/?api={}&email={}"

# Local fast checks (keep these to save credits)
DISPOSABLE_LIST_URL = 'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf'
ROLE_LIST_URL = 'https://raw.githubusercontent.com/mixmaxhq/role-based-email-addresses/master/roles.txt'
FREE_LIST_URL = 'https://raw.githubusercontent.com/Kikobeats/free-email-domains/master/domains.json'

TYPO_CORRECTIONS = {  # Common typos
    'gamil.com': 'gmail.com', 'gmial.com': 'gmail.com',
    'hotmial.com': 'hotmail.com', 'yaho.com': 'yahoo.com',
    # Add more if needed
}

disposable_domains = set()
role_prefixes = set()
free_domains = set()

def load_local_lists():
    global disposable_domains, role_prefixes, free_domains
    try:
        disposable_domains = {line.strip().lower() for line in requests.get(DISPOSABLE_LIST_URL).text.splitlines() if line.strip()}
        role_prefixes = {line.strip().lower() for line in requests.get(ROLE_LIST_URL).text.splitlines() if line.strip()}
        free_json = requests.get(FREE_LIST_URL).json()
        free_domains = {d.lower() for d in free_json}
    except: st.warning("Local lists not loaded (offline ok, DeBounce handles most)")

def local_fast_check(email):
    email = email.strip().lower()
    domain = email.split('@')[1] if '@' in email else ''
    local = email.split('@')[0] if '@' in email else ''
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        sugg = TYPO_CORRECTIONS.get(domain)
        return 'Invalid', 'Invalid syntax', sugg or ''
    
    if domain in disposable_domains:
        return 'Invalid', 'Disposable', ''
    
    if any(local.startswith(p + sep) or local == p for p in role_prefixes for sep in ['.', '-', '_', '']):
        return 'Invalid', 'Role-based', ''
    
    if domain in free_domains:
        return 'Invalid', 'Free/personal provider', ''
    
    return None, None, None  # Proceed to DeBounce API

def debounce_verify(email):
    if not DEBounce_API_KEY:
        return 'Invalid', 'No API Key', ''
    
    url = SINGLE_ENDPOINT.format(DEBounce_API_KEY, email)
    try:
        resp = requests.get(url, timeout=15).json()['debounce']
        code = resp.get('code', '0')  # '10' valid, etc. See docs for codes
        reason_map = {
            '10': ('Valid', 'Deliverable'),
            '7': ('Invalid', 'Undeliverable'),
            '5': ('Invalid', 'Disposable'),
            '8': ('Invalid', 'Catch-all'),
            '6': ('Unknown', 'Unknown'),
            # Add more from DeBounce codes
        }
        status, reason = reason_map.get(code, ('Unknown', resp.get('reason', 'Unknown')))
        suggestion = resp.get('did_you_mean', '')
        return status, reason, suggestion
    except:
        return 'Unknown', 'API Error', ''

def verify_email(email):
    status, reason, sugg = local_fast_check(email)
    if status:
        return status, reason, sugg
    return debounce_verify(email)

# GUI
st.title("🚀 Ultimate Email Verifier - Powered by DeBounce")
st.markdown("Ultra-fast verification for thousands/millions using your DeBounce account!")

load_local_lists()

if not DEBounce_API_KEY:
    st.warning("Enter your DeBounce API Key in sidebar to start!")

uploaded_file = st.file_uploader("Upload .txt or .csv", type=['txt', 'csv'])
if uploaded_file and DEBounce_API_KEY:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        emails = df.iloc[:, 0].dropna().astype(str).unique().tolist()  # Dedup
    else:
        emails = [line.strip() for line in StringIO(uploaded_file.getvalue().decode('utf-8')) if line.strip()]
    
    st.write(f"Loaded {len(emails):,} unique emails")

    col1, col2 = st.columns(2)
    max_workers = col1.slider("Threads (API concurrent)", 5, 30, 20)
    batch_size = col2.slider("Batch size", 100, 1000, 500)

    if st.button("Start Verification"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        processed = 0
        
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i+batch_size]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(verify_email, e): e for e in batch}
                for future in as_completed(futures):
                    status, reason, sugg = future.result()
                    results.append({'Email': futures[future], 'Status': status, 'Reason': reason, 'Suggestion': sugg})
                    processed += 1
                    progress_bar.progress(processed / len(emails))
                    status_text.text(f"Processed {processed:,}/{len(emails):,}")
        
        results_df = pd.DataFrame(results)
        valid_df = results_df[results_df['Status'] == 'Valid']
        invalid_df = results_df[results_df['Status'] != 'Valid']
        
        st.success("Verification Complete!")
        st.download_button("Download Valid", valid_df.to_csv(index=False), "valid_emails.csv")
        st.download_button("Download Invalid", invalid_df.to_csv(index=False), "invalid_emails.csv")
        st.dataframe(results_df)

else:
    st.info("Upload file + add API Key to start!")