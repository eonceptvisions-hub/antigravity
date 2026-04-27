import backend
import sys
import json

def main():
    if len(sys.argv) < 3:
        print("Usage: python update_vault.py <lead_id_or_name> <json_updates>")
        print("Example: python update_vault.py \"Helion Venture Partners\" '{\"website\": \"www.helionvc.com\", \"contact_email\": \"contact@helionvc.com\"}'")
        return

    selector = sys.argv[1]
    try:
        updates = json.loads(sys.argv[2])
    except json.JSONDecodeError:
        print("Error: Invalid JSON for updates.")
        return

    df = backend.load_vault()
    if df is None:
        print("Error: Vault not found.")
        return

    # Try matching by ID first, then by name
    mask = (df['id'] == selector) | (df['name'] == selector)
    if not mask.any():
        print(f"Error: Lead '{selector}' not found in vault.")
        return

    indices = df.index[mask].tolist()
    for idx in indices:
        lead_id = df.at[idx, 'id']
        lead_name = df.at[idx, 'name']
        print(f"Updating lead: {lead_name} ({lead_id})")
        
        for field, value in updates.items():
            if field in df.columns:
                print(f"  {field}: {df.at[idx, field]} -> {value}")
                df.at[idx, field] = value
            else:
                print(f"  Warning: Field '{field}' not found in schema.")

    backend.save_vault(df)
    print("Vault updated successfully.")

if __name__ == "__main__":
    main()
