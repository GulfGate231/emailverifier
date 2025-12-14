import re
import dns.resolver
import smtplib
import socket
import time
import requests
import csv
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Config
INPUT_FILE = 'emails.csv'                  # Can be .txt or .csv (one email per line or in first column)
VALID_OUTPUT = 'valid_emails.csv'
INVALID_OUTPUT = 'invalid_emails.csv'
LOG_FILE = 'verification_log.txt'
DISPOSABLE_LIST_URL = 'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf'
ROLE_LIST_URL = 'https://raw.githubusercontent.com/mixmaxhq/role-based-email-addresses/master/roles.txt'  # ~400 common roles
SENDER_EMAIL = 'verifier@example.com'      # Fake sender
TIMEOUT = 10                               # Connection timeout
MAX_WORKERS = 20                           # Parallel threads
BATCH_SIZE = 100                           # 0 = no batching
DELAY_BETWEEN_BATCHES = 10                 # Seconds
EMAIL_COLUMN = 0                           # Column index for email in CSV (0 = first column)

disposable_domains = set()
role_prefixes = set()

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as logf:
        logf.write(log_entry)

def load_disposable_domains():
    global disposable_domains
    log_message("Downloading latest disposable domains list...")
    try:
        response = requests.get(DISPOSABLE_LIST_URL, timeout=15)
        response.raise_for_status()
        disposable_domains = {line.strip().lower() for line in response.text.splitlines() if line.strip()}
        log_message(f"Loaded {len(disposable_domains)} disposable domains.")
    except Exception as e:
        log_message(f"Warning: Could not download disposable list ({e}). Continuing without.")

def load_role_prefixes():
    global role_prefixes
    log_message("Downloading latest role-based prefixes list...")
    try:
        response = requests.get(ROLE_LIST_URL, timeout=15)
        response.raise_for_status()
        role_prefixes = {line.strip().lower() for line in response.text.splitlines() if line.strip()}
        log_message(f"Loaded {len(role_prefixes)} role-based prefixes.")
    except Exception as e:
        log_message(f"Warning: Could not download role list ({e}). Continuing without role detection.")

def is_disposable(email):
    domain = email.split('@')[1].lower()
    return domain in disposable_domains

def is_role_based(email):
    local_part = email.split('@')[0].lower()
    # Check if local_part starts with any role prefix (or exact match)
    return any(local_part == prefix or local_part.startswith(prefix + '.') or local_part.startswith(prefix + '-') or local_part.startswith(prefix + '_') for prefix in role_prefixes)

def is_valid_syntax(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email.strip()) is not None

def get_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_hosts = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in records])
        return [host for _, host in mx_hosts]
    except Exception:
        return None

def smtp_verify(email, mx_host):
    try:
        server = smtplib.SMTP(mx_host, timeout=TIMEOUT)
        server.ehlo_or_helo_if_needed()
        server.mail(SENDER_EMAIL)
        code, _ = server.rcpt(email)
        server.quit()
        return code in (250, 251)
    except Exception:
        return False

def verify_email(email):
    email = email.strip().lower()
    if not email or not is_valid_syntax(email):
        return False, "Invalid syntax"
    
    if is_disposable(email):
        return False, "Disposable/temporary email"
    
    if is_role_based(email):
        return False, "Role-based email (generic/group)"
    
    domain = email.split('@')[1]
    mx_hosts = get_mx_record(domain)
    if not mx_hosts:
        return False, "No MX record (domain inactive)"
    
    for mx in mx_hosts[:3]:
        if smtp_verify(email, mx):
            return True, "Valid (SMTP accepted)"
        time.sleep(0.2)
    
    return False, "Invalid (SMTP rejected/no response)"

def load_emails_from_file():
    emails = []
    ext = os.path.splitext(INPUT_FILE)[1].lower()
    
    if ext == '.csv':
        try:
            with open(INPUT_FILE, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) > EMAIL_COLUMN:
                        email = row[EMAIL_COLUMN].strip()
                        if email:
                            emails.append(email)
        except Exception as e:
            log_message(f"Error reading CSV: {e}")
    else:  # .txt or others
        try:
            with open(INPUT_FILE, 'r', encoding='utf-8') as f:
                emails = [line.strip() for line in f if line.strip()]
        except Exception as e:
            log_message(f"Error reading file: {e}")
    
    return emails

def save_csv_results(valid, invalid):
    # Valid
    with open(VALID_OUTPUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Email', 'Status', 'Reason'])
        for email, reason in valid:
            writer.writerow([email, 'Valid', reason])
    
    # Invalid
    with open(INVALID_OUTPUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Email', 'Status', 'Reason'])
        for email, reason in invalid:
            writer.writerow([email, 'Invalid', reason])

def main():
    open(LOG_FILE, 'w').close()  # Clear log
    log_message("=== Email Verification Started ===")
    
    load_disposable_domains()
    load_role_prefixes()
    
    emails = load_emails_from_file()
    if not emails:
        log_message("No emails found in input file.")
        return
    
    total = len(emails)
    log_message(f"Loaded {total} emails from {INPUT_FILE}")
    
    valid = []
    invalid = []
    processed = 0
    
    for i in range(0, total, BATCH_SIZE if BATCH_SIZE > 0 else total):
        batch = emails[i:i + (BATCH_SIZE if BATCH_SIZE > 0 else total)]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_email = {executor.submit(verify_email, email): email for email in batch}
            
            for future in as_completed(future_to_email):
                email = future_to_email[future]
                is_valid, reason = future.result()
                processed += 1
                status_msg = f"[{processed}/{total}] {email} - {'Valid' if is_valid else 'Invalid'}: {reason}"
                log_message(status_msg)
                
                if is_valid:
                    valid.append((email, reason))
                else:
                    invalid.append((email, reason))
        
        if BATCH_SIZE > 0 and i + BATCH_SIZE < total:
            log_message(f"Batch complete. Waiting {DELAY_BETWEEN_BATCHES}s before next...")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    save_csv_results(valid, invalid)
    
    log_message("\n=== Verification Complete ===")
    log_message(f"Valid: {len(valid)} → {VALID_OUTPUT}")
    log_message(f"Invalid: {len(invalid)} → {INVALID_OUTPUT}")
    log_message(f"Full log saved to {LOG_FILE}")

if __name__ == "__main__":
    main()