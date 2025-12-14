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

# URLs for lists
DISPOSABLE_LIST_URL = 'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf'
ROLE_LIST_URL = 'https://raw.githubusercontent.com/mixmaxhq/role-based-email-addresses/master/roles.txt'
FREE_LIST_URL = 'https://raw.githubusercontent.com/Kikobeats/free-email-domains/master/domains.json'

# Common typo mappings + popular domains for distance checks
TYPO_CORRECTIONS = {
    'gamil.com': 'gmail.com', 'gmial.com': 'gmail.com', 'gmai.com': 'gmail.com',
    'hotmial.com': 'hotmail.com', 'hotmai.com': 'hotmail.com',
    'yaho.com': 'yahoo.com', 'yahhoo.com': 'yahoo.com',
    'outllok.com': 'outlook.com', 'outlok.com': 'outlook.com',
    'protontmail.com': 'protonmail.com', 'protomail.com': 'protonmail.com',
}
POPULAR_DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com', 'protonmail.com']

disposable_domains = set()
role_prefixes = set()
free_domains = set()

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def get_typo_suggestion(domain):
    domain = domain.lower()
    if domain in TYPO_CORRECTIONS:
        return TYPO_CORRECTIONS[domain]
    for pop in POPULAR_DOMAINS:
        if levenshtein_distance(domain, pop) <= 1:
            return pop
    return None

@st.cache_data(ttl=86400)  # Cache for 24h
def load_lists():
    global disposable_domains, role_prefixes, free_domains
    try:
        disp = requests.get(DISPOSABLE_LIST_URL).text.splitlines()
        disposable_domains = {d.lower() for d in disp if d.strip()}
    except: st.error("Failed to load disposable list.")
    
    try:
        roles = requests.get(ROLE_LIST_URL).text.splitlines()
        role_prefixes = {r.lower() for r in roles if r.strip()}
    except: st.error("Failed to load role list.")
    
    try:
        free_json = requests.get(FREE_LIST_URL).json()
        free_domains = {d.lower() for d in free_json}
    except: st.error("Failed to load free email list.")

def is_disposable(domain): return domain in disposable_domains
def is_role_based(local): return any(local.startswith(p + '.') or local.startswith(p + '-') or local.startswith(p + '_') or local == p for p in role_prefixes)
def is_free_email(domain): return domain in free_domains

def is_valid_syntax(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)

def get_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_hosts = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in records])
        return [host for _, host in mx_hosts]
    except: return None

def smtp_verify(email, mx_host, timeout=10):
    try:
        server = smtplib.SMTP(mx_host, timeout=timeout)
        server.ehlo_or_helo_if_needed()
        server.mail('verifier@example.com')
        code, _ = server.rcpt(email)
        server.quit()
        return code in (250, 251)
    except: return False

def verify_email(email):
    email = email.strip().lower()
    domain = email.split('@')[1] if '@' in email else ''
    local = email.split('@')[0] if '@' in email else ''
    
    suggestion = None
    if not is_valid_syntax(email):
        if domain:
            suggestion = get_typo_suggestion(domain)
        return 'Invalid', 'Invalid syntax', suggestion
    
    if is_disposable(domain):
        return 'Invalid', 'Disposable/temporary email', suggestion
    
    if is_role_based(local):
        return 'Invalid', 'Role-based email', suggestion
    
    if is_free_email(domain):
        return 'Invalid', 'Free/personal email provider', suggestion
    
    mx_hosts = get_mx_record(domain)
    if not mx_hosts:
        suggestion = get_typo_suggestion(domain)
        return 'Invalid', 'No MX record', suggestion
    
    for mx in mx_hosts[:3]:
        if smtp_verify(email, mx):
            return 'Valid', 'Valid (SMTP accepted)', suggestion
        time.sleep(0.2)
    
    return 'Invalid', 'Invalid (SMTP rejected/no response)', suggestion

st.title("🚀 Ultimate Email Verifier Pro")
st.markdown("Verify thousands of emails with deep checks + disposable/role/free detection + typo suggestions!")

load_lists()

uploaded_file = st.file_uploader("Upload emails.txt or emails.csv (email in first column)", type=['txt', 'csv'])
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        emails = df.iloc[:, 0].dropna().astype(str).tolist()
    else:
        string_data = StringIO(uploaded_file.getvalue().decode('utf-8'))
        emails = [line.strip() for line in string_data if line.strip()]
    
    st.write(f"Loaded {len(emails)} emails")

    col1, col2 = st.columns(2)
    max_workers = col1.slider("Threads", 5, 50, 20)
    batch_size = col2.slider("Batch size (0 = no batching)", 0, 500, 100)
    delay = col1.slider("Delay between batches (sec)", 0, 60, 10)
    timeout = col2.slider("SMTP timeout (sec)", 5, 30, 10)

    if st.button("Start Verification"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        processed = 0
        
        for i in range(0, len(emails), batch_size if batch_size > 0 else len(emails)):
            batch = emails[i:i + (batch_size if batch_size > 0 else len(emails))]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(verify_email, e): e for e in batch}
                for future in as_completed(futures):
                    status, reason, sugg = future.result()
                    results.append({'Email': futures[future], 'Status': status, 'Reason': reason, 'Suggestion': sugg or ''})
                    processed += 1
                    progress_bar.progress(processed / len(emails))
                    status_text.text(f"Processed {processed}/{len(emails)}")
            
            if batch_size > 0 and i + batch_size < len(emails):
                time.sleep(delay)
        
        results_df = pd.DataFrame(results)
        valid_df = results_df[results_df['Status'] == 'Valid']
        invalid_df = results_df[results_df['Status'] == 'Invalid']
        
        st.success("Verification Complete!")
        st.download_button("Download Valid Emails", valid_df.to_csv(index=False), "valid_emails.csv")
        st.download_button("Download Invalid Emails", invalid_df.to_csv(index=False), "invalid_emails.csv")
        
        st.dataframe(results_df)

else:
    st.info("Upload a file to get started!")