import time
import re
import socket
import smtplib
import dns.resolver
from googlesearch import search
from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Optional
import database

# --- Scraper Logic ---

def scrape_google_xray(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Scrapes Google using X-Ray search strings.
    Example query: 'site:linkedin.com/in/ "Software Engineer" "San Francisco"'
    """
    results = []
    try:
        # Using googlesearch-python
        for url in search(query, num_results=num_results, sleep_interval=2):
            # For each URL, we could attempt to fetch details, 
            # but for X-Ray, often the snippet is enough or we just need the URL/Name.
            # Here we just track the URL and a placeholder for name/company.
            results.append({
                "url": url,
                "source": "Google X-Ray"
            })
    except Exception as e:
        print(f"Scrape Error: {e}")
    
    return results

# --- Permutation Logic ---

def generate_email_patterns(name: str, domain: str) -> List[str]:
    """Generates common business email permutations."""
    if not name or not domain:
        return []
    
    parts = name.lower().split()
    if len(parts) < 2:
        first, last = parts[0], ""
    else:
        first, last = parts[0], parts[-1]
    
    domain = domain.lower().replace("http://", "").replace("https://", "").replace("www.", "").split('/')[0]
    
    patterns = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}{last[0]}@{domain}",
        f"{first}_{last}@{domain}",
        f"{last}@{domain}"
    ]
    return list(set(patterns))

# --- Verification Logic ---

def verify_email_smtp(email: str, sender_email: str = "verify@example.com") -> str:
    """
    Verifies email address using DNS MX lookup and SMTP handshake.
    Returns: 'VALID', 'INVALID', or 'RISKY' (e.g. Catch-all or Timeout)
    """
    try:
        domain = email.split('@')[1]
        # 1. DNS MX Lookup
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = sorted(records, key=lambda r: r.preference)[0].exchange.to_text()
        
        # 2. SMTP Handshake
        host = socket.gethostname()
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(0)
        
        server.connect(mx_record)
        server.helo(host)
        server.mail(sender_email)
        code, message = server.rcpt(email)
        server.quit()
        
        if code == 250:
            return 'VALID'
        elif code == 550:
            return 'INVALID'
        else:
            return 'RISKY'
            
    except Exception as e:
        print(f"Verification error for {email}: {e}")
        return 'RISKY'

# --- Main Workflow ---

def ingest_leads_workflow(search_query: str, domain: str):
    print(f"Starting ingestion for: {search_query}")
    raw_results = scrape_google_xray(search_query, num_results=5)
    
    for res in raw_results:
        # In a real scenario, we'd extract specific names from the landing page
        # For this demo/skeleton, we use placeholder names if not found
        name = "Lead Candidate" 
        company = domain.split('.')[0].capitalize()
        
        patterns = generate_email_patterns(name, domain)
        for email in patterns:
            print(f"Verifying {email}...")
            status = verify_email_smtp(email)
            if status == 'VALID':
                print(f"Found VALID email: {email}")
                database.add_lead(name, company, "Prospect", email, "Google X-Ray", status)
                break # Move to next lead
            elif status == 'RISKY':
                 database.add_lead(name, company, "Prospect", email, "Google X-Ray", status)

if __name__ == "__main__":
    # Test Run
    # Warning: Real SMTP verification can be flagged as spam activity.
    # Use sparingly.
    pass
