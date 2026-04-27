import backend
import pandas as pd

def test_prediction():
    print("--- Testing Smart Prediction & Verification ---")
    
    # Test Job Hunting (Recruiting)
    print("\n[JOB_HUNTING Mode]")
    email = backend.predict_and_verify_email("John Doe", "google.com", "JOB_HUNTING")
    print(f"Predicted Email for John Doe @ google.com: {email}")
    
    # Test Business Sales (CEO/CFO)
    print("\n[BUSINESS_SALES Mode]")
    email = backend.predict_and_verify_email("John Doe", "microsoft.com", "BUSINESS_SALES")
    print(f"Predicted Email for John Doe @ microsoft.com: {email}")

    # Test SMTP Direct logic (Safe check with non-existent)
    print("\n[SMTP Direct Check]")
    status = backend.verify_email_smtp_direct("nonexistent.random.12345@gmail.com")
    print(f"Status for nonexistent.random.12345@gmail.com: {status}")

if __name__ == "__main__":
    test_prediction()
