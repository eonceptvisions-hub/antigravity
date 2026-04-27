import backend
import json

updates = {
    "website": "www.helionvc.com",
    "contact_email": "contact@helionvc.com",
    "phone": "(0124) 4615333"
}

df = backend.load_vault()
if df is not None:
    mask = df['name'] == "Helion Venture Partners"
    if mask.any():
        indices = df.index[mask].tolist()
        for idx in indices:
            for field, value in updates.items():
                if field in df.columns:
                    df.at[idx, field] = value
        backend.save_vault(df)
        print("Updated Helion Venture Partners successfully.")
    else:
        print("Helion Venture Partners not found.")
else:
    print("Vault not found.")
