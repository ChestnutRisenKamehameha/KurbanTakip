"""Temporary test: V2.1 -> V2.2 migration."""
import sqlite3, os
from database import APP_DIR, initialise_database

test_db = APP_DIR / "migration_test.db"
if test_db.exists():
    os.remove(str(test_db))

# Create a fake V2.1 DB with is_paid column
conn = sqlite3.connect(str(test_db))
conn.executescript("""
CREATE TABLE animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slaughter_date DATE NOT NULL,
    total_price_kurus INTEGER NOT NULL DEFAULT 0,
    total_weight_grams INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE shareholders (phone TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE animal_shares (
    animal_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT 0,
    share_fraction INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (animal_id, phone)
);
INSERT INTO animals VALUES (1, '2026-06-15', 2100000, 350000);
INSERT INTO shareholders VALUES ('+905551234567', 'Ali');
INSERT INTO shareholders VALUES ('+905559999999', 'Veli');
INSERT INTO animal_shares VALUES (1, '+905551234567', 1, 3);
INSERT INTO animal_shares VALUES (1, '+905559999999', 0, 4);
""")
conn.commit()
conn.close()
print("V2.1 DB created (is_paid column)")

# Run migration
initialise_database(test_db)

# Verify
conn = sqlite3.connect(str(test_db))
conn.row_factory = sqlite3.Row
cols = [r[1] for r in conn.execute("PRAGMA table_info(animal_shares)").fetchall()]
print(f"After migration: {cols}")
assert "paid_amount_kurus" in cols, "paid_amount_kurus missing"
assert "is_paid" not in cols, "is_paid still exists"

rows = conn.execute("SELECT * FROM animal_shares ORDER BY phone").fetchall()

# Ali: is_paid=1, frac=3, total_frac=7, price=2100000 -> 2100000*3/7=900000
ali = [r for r in rows if r["phone"] == "+905551234567"][0]
assert ali["paid_amount_kurus"] == 900000, f"Got {ali['paid_amount_kurus']}"
print(f"Ali: {ali['paid_amount_kurus']} kurus (expected 900000) OK")

# Veli: is_paid=0 -> 0
veli = [r for r in rows if r["phone"] == "+905559999999"][0]
assert veli["paid_amount_kurus"] == 0
print(f"Veli: {veli['paid_amount_kurus']} kurus (expected 0) OK")

conn.close()
os.remove(str(test_db))
print("\n=== MIGRATION V2.1->V2.2 PASSED ===")
