import streamlit as st
import pandas as pd
import re
import dns.resolver
import smtplib
import socket
import time
import requests
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# Ultra caching
@lru_cache(maxsize=10000)
def get_mx_record_cached(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX', lifetime=8)
        mx_hosts = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in records])
        return [host for _, host in mx_hosts[:2]]  # Top 2 only
    except:
        return None

# Load lists once
@st.cache_data(ttl=86400)
def load_lists():
    disposable, role, free = set(), set(), set()
    try:
        disposable = {l.lower().strip() for l in requests.get(
            'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf', timeout=10).text.splitlines() if l.strip()}
        role = {l.lower().strip() for l in requests.get(
            'https://raw.githubusercontent.com/mixmaxhq/role-based-email-addresses/master/roles.txt', timeout=10).text.splitlines() if l.strip()}
        free_json = requests.get('https://raw.githubusercontent.com/Kikobeats/free-email-domains/master/domains.json', timeout=10).json()
        free = {d.lower() for d in free_json}
    except:
        st.error("Failed to load lists — continuing with basic checks.")
    return disposable, role, free

disposable_domains, role_prefixes, free_domains = load_lists()

def is_valid_syntax(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip()) is not None

def fast_check(email):
    email = email.strip().lower()
    if not email or not is_valid_syntax(email):
        return 'Invalid', 'Invalid syntax'
    
    domain = email.split('@')[1]
    local = email.split('@')[0]
    
    if domain in disposable_domains:
        return 'Invalid', 'Disposable'
    
    if any(local == p or local.startswith(p + sep) for p in role_prefixes for sep in ['.', '-', '_']):
        return 'Invalid', 'Role-based'
    
    if domain in free_domains:
        return 'Invalid', 'Free/personal provider (skipped SMTP)'  # BIG speed win
    
    return None, None

def smtp_verify_max(email, mx_host):
    try:
        server = smtplib.SMTP(mx_host, timeout=6)  # Aggressive timeout
        server.ehlo_or_helo_if_needed()
        server.mail('check@example.com')
        code, _ = server.rcpt(email)
        server.quit()
        return code in (250, 251)
    except:
        return False

def verify_email(email):
    status, reason = fast_check(email)
    if status:
        return status, reason
    
    domain = email.lower().split('@')[1]
    mx_hosts = get_mx_record_cached(domain)
    if not mx_hosts:
        return 'Invalid', 'No MX record'
    
    # Try ONLY the primary MX
    if smtp_verify_max(email.lower(), mx_hosts[0]):
        return 'Valid', 'Deliverable'
    
    return 'Invalid', 'Undeliverable'

# GUI
st.title("⚡ MAX SPEED Email Verifier (Pushed to Limit)")
st.markdown("Ultra-optimized: caching, free-provider skip, 1 MX try, low timeout — fastest self-hosted possible!")

uploaded_file = st.file_uploader("Upload .txt or .csv", type=['txt', 'csv'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        emails = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    else:
        emails = list(set(line.strip().lower() for line in StringIO(uploaded_file.getvalue().decode('utf-8')) if line.strip()))
    
    st.write(f"Loaded {len(emails):,} unique emails (deduped)")

    threads = st.slider("Threads (max safe on VPS)", 20, 60, 50)  # Push it!

    if st.button("🚀 START MAX VERIFICATION"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        processed = 0
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(verify_email, e): e for e in emails}
            for future in as_completed(futures):
                status, reason = future.result()
                results.append({'Email': futures[future], 'Status': status, 'Reason': reason})
                processed += 1
                progress_bar.progress(processed / len(emails))
                status_text.text(f"Blazing: {processed:,}/{len(emails):,} — Est. {((len(emails)-processed)/(processed/max(1,(time.time()-start_time))) if processed > 100 else 0):.0f}s left")
        
        start_time = time.time()  # For ETA (approx)
        
        results_df = pd.DataFrame(results)
        valid_df = results_df[results_df['Status'] == 'Valid']
        invalid_df = results_df[results_df['Status'] == 'Invalid']
        
        st.success("MAX VERIFICATION COMPLETE!")
        st.download_button("Download Valid", valid_df.to_csv(index=False), "valid_max.csv")
        st.download_button("Download Invalid", invalid_df.to_csv(index=False), "invalid_max.csv")
        st.dataframe(results_df)

else:
    st.info("Upload your list — this version is tuned for max speed!")