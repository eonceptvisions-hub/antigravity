import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "leads.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create leads table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        company TEXT,
        role TEXT,
        email TEXT UNIQUE,
        verification_status TEXT DEFAULT 'PENDING',
        source TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create outreach_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS outreach_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT NOT NULL,
        user_id TEXT,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_lead(name: str, company: str, role: str, email: str, source: str, verification_status: str = 'PENDING'):
    conn = get_connection()
    cursor = conn.cursor()
    lead_id = str(uuid.uuid4())
    try:
        cursor.execute('''
        INSERT INTO leads (id, name, company, role, email, source, verification_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (lead_id, name, company, role, email, source, verification_status))
        conn.commit()
        return lead_id
    except sqlite3.IntegrityError:
        # Handle duplicate email
        return None
    finally:
        conn.close()

def update_lead_status(lead_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE leads SET verification_status = ? WHERE id = ?', (status, lead_id))
    conn.commit()
    conn.close()

def log_outreach(lead_id: str, user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO outreach_logs (lead_id, user_id) VALUES (?, ?)', (lead_id, user_id))
    conn.commit()
    conn.close()

def get_all_leads() -> List[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leads ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
