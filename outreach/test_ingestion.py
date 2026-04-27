import ingestion
import database
import sys

def run_test():
    print("--- Ingestion Engine Test ---")
    database.init_db()
    
    # Test Pattern Generation
    patterns = ingestion.generate_email_patterns("John Doe", "google.com")
    print(f"Patterns for John Doe @ google.com: {patterns}")
    
    # Test SMTP Verification (Safe check)
    # We'll use a known non-existent pattern to see if it catches 'INVALID' or 'RISKY'
    test_email = "nonexistent.user.123456@gmail.com"
    print(f"Testing verification for {test_email}...")
    status = ingestion.verify_email_smtp(test_email)
    print(f"Status for {test_email}: {status}")
    
    # Test Database Insertion
    lead_id = database.add_lead("Test Lead", "Test Co", "Tester", "test@example.com", "Manual Test")
    if lead_id:
        print(f"Successfully added test lead: {lead_id}")
    else:
        print("Lead already exists or insertion failed.")

    print("\n--- Current Leads in DB ---")
    leads = database.get_all_leads()
    for l in leads:
        print(f"{l['name']} | {l['email']} | {l['verification_status']}")

if __name__ == "__main__":
    run_test()
