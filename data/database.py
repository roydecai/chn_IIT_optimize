import sqlite3
from pathlib import Path
from decimal import Decimal
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "company.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            level INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            vat_rate REAL,
            surtax_rate REAL,
            eit_rate REAL,
            pit_rate REAL,
            is_vat_general_taxpayer INTEGER DEFAULT 0,
            parent_code TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            description TEXT,
            effective_date DATE,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hhy_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hhy_code TEXT NOT NULL,
            rule_version TEXT NOT NULL,
            allocations TEXT NOT NULL,
            income_nature TEXT NOT NULL,
            merge_policy TEXT NOT NULL,
            validation_rules TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rule_version) REFERENCES rule_versions(version)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flow_constraints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_company TEXT NOT NULL,
            to_company TEXT NOT NULL,
            max_amount REAL DEFAULT 500000,
            constraint_type TEXT DEFAULT 'annual_limit',
            rule_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    existing = cursor.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    if existing == 0:
        seed_data(cursor)
    
    conn.commit()
    conn.close()

def seed_data(cursor):
    companies = [
        ("PXA", "PXA公司", 1, "company", 0.06, 0.12, 0.25, None, 1, None, "资金源头1"),
        ("PXU", "PXU公司", 1, "company", 0.06, 0.12, 0.25, None, 1, None, "资金源头2"),
        ("KKG", "KKG公司", 2, "company", 0.06, 0.12, 0.25, None, 1, "PXA", "中间公司"),
        ("PYU", "PYU公司", 2, "company", 0.06, 0.12, 0.25, None, 1, "PXU", "中间公司"),
        ("HHY", "HHY合伙", 3, "partnership", None, None, None, None, 0, "KKG", "Pass-through实体"),
        ("HHY2", "HHY2合伙", 3, "partnership", None, None, None, None, 0, "PYU", "Pass-through实体"),
        ("SZW", "SZW自然人", 4, "individual", None, None, None, 0.20, 0, "HHY", "终点自然人1 - 综合所得"),
        ("SXP", "SXP自然人", 4, "individual", None, None, None, 0.20, 0, "HHY2", "终点自然人2 - 独立镜像"),
    ]
    
    cursor.executemany("""
        INSERT INTO companies (code, name, level, entity_type, vat_rate, surtax_rate, eit_rate, pit_rate, is_vat_general_taxpayer, parent_code, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, companies)
    
    cursor.execute("""
        INSERT INTO rule_versions (version, description, effective_date, is_active)
        VALUES ('v1.0', '初始版本', '2026-01-01', 1)
    """)
    
    hhy_rules = [
        ("HHY", "v1.0", '{"SZW": 1.0}', '{"SZW": "comprehensive"}', '{"merge_to_szw": true, "bonus_special_tax": false}', '{"min_ratio": 0, "max_ratio": 1}'),
        ("HHY2", "v1.0", '{"SXP": 1.0}', '{"SXP": "comprehensive"}', '{"merge_to_szw": false, "bonus_special_tax": false}', '{"min_ratio": 0, "max_ratio": 1}'),
    ]
    
    cursor.executemany("""
        INSERT INTO hhy_rules (hhy_code, rule_version, allocations, income_nature, merge_policy, validation_rules)
        VALUES (?, ?, ?, ?, ?, ?)
    """, hhy_rules)
    
    constraints = [
        ("PXA", "KKG", 500000, "annual_limit", "v1.0"),
        ("PXU", "PYU", 500000, "annual_limit", "v1.0"),
    ]
    
    cursor.executemany("""
        INSERT INTO flow_constraints (from_company, to_company, max_amount, constraint_type, rule_version)
        VALUES (?, ?, ?, ?, ?)
    """, constraints)

def get_company_by_code(code: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM companies WHERE code = ?", (code,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_companies() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM companies ORDER BY level, code").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_hhy_rule(hhy_code: str, version: str = "v1.0") -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("""
        SELECT * FROM hhy_rules WHERE hhy_code = ? AND rule_version = ?
    """, (hhy_code, version)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_flow_constraint(from_code: str, to_code: str, version: str = "v1.0") -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("""
        SELECT * FROM flow_constraints 
        WHERE from_company = ? AND to_company = ? AND (rule_version = ? OR rule_version IS NULL)
    """, (from_code, to_code, version)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_active_rule_version() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT version FROM rule_versions WHERE is_active = 1").fetchone()
    conn.close()
    return row[0] if row else "v1.0"

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
