# Outreach Brain: Improvements & Issues List

This document tracks current limitations, bugs, and proposed enhancements for the Outreach Brain application.

## 🔴 High Priority (Bugs & Critical Issues)

### 1. Lead Deduplication Logic
- **Issue**: The current logic `drop_duplicates(subset=['id', 'contact_email', 'name'])` is ineffective because `id` is a newly generated UUID for every search result.
- **Impact**: Duplicate leads appear in the vault if searched multiple times.
- **Fix**: Deduplicate based on `['name', 'company']` or `['website']`.

### 2. Search Grounding Reliability
- **Issue**: The `google_search` tool configuration in `backend.py` might be incompatible with certain SDK versions or API key restrictions.
- **Impact**: "Execute Global Research" may fail with "Unknown field" or "Method not found" errors.
- **Fix**: Standardize tool declaration and add robust error reporting.

### 3. Loop Performance
- **Issue**: `fill_missing_info` and `generate_email_drafts` process rows one by one.
- **Impact**: Extremely slow for vaults with >20 leads.
- **Fix**: Implement concurrent processing or batch LLM calls.

---

## 🟡 Medium Priority (Feature Enhancements)

### 1. Advanced Analytics
- **Issue**: Current analytics are just a count of statuses.
- **Fix**: Add success rates, company-wise breakdowns, and "Intel Saturation" progress tracking over time.

### 2. Email Prediction Fallbacks
- **Issue**: Fallback is hardcoded to `info@{domain}` or `careers@{domain}`.
- **Fix**: Use patterns like `{first}.{last}@{domain}` or check common naming conventions via OSINT.

### 3. Draft Customization
- **Issue**: Email drafts use a fixed prompt template.
- **Fix**: Allow users to choose "Tone of Voice", "Length", and "Custom Call to Action".

### 4. Better File Extraction
- **Issue**: `extract_text_from_file` only handles basic PDF/Word text.
- **Fix**: Add OCR support for scanned documents and better table handling.

---

## 🔵 Low Priority (DX & Polish)

### 1. Secure Credential Handling
- **Issue**: Keys are stored in plaintext `session_state`.
- **Fix**: Integrate with a secrets manager or local encrypted storage.

### 2. UI Polish
- **Issue**: Some redundant code in `app.py` (e.g., double `st.rerun()`).
- **Fix**: Clean up event handling and state transitions.

### 3. Export Capabilities
- **Issue**: Only `vault.csv` is supported.
- **Fix**: Add Excel and JSON export options for processed leads.
