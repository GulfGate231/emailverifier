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

# Fast caching for DNS and domains
@lru_cache(maxsize=5000)
def get_mx_record_cached(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX', lifetime=10)
        mx_hosts = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in records])
        return [host for _, host in mx_hosts[:3]]  # Limit to top 3
    except:
        return None

# Lists (cached)
@st.cache_data(ttl=86400)
def load_lists():
    disposable = set()
    role = set()
    free = set()
    try:
        disposable = {l.lower() for l in requests.get(
            'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf').text.splitlines() if l.strip()}
        role = {l.lower() for l in requests.get(
            'https://raw.githubusercontent.com/mixmaxhq/role-based-email-addresses/master/roles.txt').text.splitlines() if l.strip()}
        free_json = requests.get('https://raw.githubusercontent.com/Kikobeats/free-email-domains/master/domains.json').json()
        free = {d.lower() for d in free_json}
    except:
        st.warning("Could not load online lists — using basic checks only.")
    return disposable, role, free

disposable_domains, role_prefixes, free_domains = load_lists()

TYPO_CORRECTIONS = {
    'gamil.com': 'gmail.com', 'gmial.com': 'gmail.com', 'gmai.com': 'gmail.com',
    'hotmial.com': 'hotmail.com', 'hotmai.com': 'hotmail.com',
    'yaho.com': 'yahoo.com', 'yahhoo.com': 'yahoo.com',
    'outllok.com': 'outlook.com', 'outlok.com': 'outlook.com',
}

POPULAR_DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'protonmail.com']

def levenshtein(a, b):
    if len(a) < len(b): return levenshtein(b, a)
    if len(b) == 0: return len(a)
    prev = list(range(len(b) + 1))
    for i, c1 in enumerate(a):
        curr = [i + 1]
        for j, c2 in enumerate(b):
            curr.append(min(curr[-1] + 1, prev[j + 1] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]

def get_typo_suggestion(domain):
    domain = domain.lower()
    if domain in TYPO_CORRECTIONS:
        return TYPO_CORRECTIONS[domain]
    for pop in POPULAR_DOMAINS:
        if levenshtein(domain, pop) <= 1:
            return pop
    return None

def is_valid_syntax(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip()) is not None

def fast_invalid_check(email):
    email = email.strip().lower()
    if not email or not is_valid_syntax(email):
        domain = email.split('@')[1] if '@' in email else ''
        sugg = get_typo_suggestion(domain) if domain else ''
        return 'Invalid', 'Invalid syntax', sugg
    
    domain = email.split('@')[1]
    local = email.split('@')[0]
    
    if domain in disposable_domains:
        return 'Invalid', 'Disposable', ''
    
    if any(local.startswith(p + sep) or local == p for p in role_prefixes for sep in ['.', '-', '_', '']):
        return 'Invalid', 'Role-based', ''
    
    if domain in free_domains:
        return 'Invalid', 'Free/personal provider', ''  # Skip SMTP for free providers
    
    return None, None, None

def smtp_verify_fast(email, mx_host):
    try:
        server = smtplib.SMTP(mx_host, timeout=8)  # Faster timeout
        server.ehlo_or_helo_if_needed()
        server.mail('verifier@example.com')
        code, _ = server.rcpt(email)
        server.quit()
        return code in (250, 251)
    except:
        return False

def verify_email(email):
    status, reason, sugg = fast_invalid_check(email)
    if status:
        return status, reason, sugg or ''
    
    email_lower = email.lower()
    domain = email_lower.split('@')[1]
    
    mx_hosts = get_mx_record_cached(domain)
    if not mx_hosts:
        sugg = get_typo_suggestion(domain)
        return 'Invalid', 'No MX record', sugg or ''
    
    # Try only first 2 MX hosts
    for mx in mx_hosts[:2]:
        if smtp_verify_fast(email_lower, mx):
            return 'Valid', 'Deliverable (SMTP accepted)', ''
    
    return 'Invalid', 'Undeliverable (SMTP rejected)', ''

# GUI
st.title("⚡ Super Fast Email Verifier (Self-Hosted)")
st.markdown("Optimized for speed: domain caching, early skips, faster timeouts — no API needed!")

uploaded_file = st.file_uploader("Upload .txt or .csv (email in first column)", type=['txt', 'csv'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        emails = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    else:
        emails = [line.strip() for line in StringIO(uploaded_file.getvalue().decode('utf-8')) if line.strip()]
    
    st.write(f"Loaded {len(emails):,} unique emails")

    col1, col2 = st.columns(2)
    max_workers = col1.slider("Threads (higher = faster)", 10, 50, 30)  # Safe to go higher now
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
        invalid_df = results_df[results_df['Status'] == 'Invalid']
        
        st.success("Verification Complete!")
        st.download_button("Download Valid Emails", valid_df.to_csv(index=False), "valid_fast.csv")
        st.download_button("Download Invalid Emails", invalid_df.to_csv(index=False), "invalid_fast.csv")
        st.dataframe(results_df)

else:
    st.info("Upload your email list to start!")