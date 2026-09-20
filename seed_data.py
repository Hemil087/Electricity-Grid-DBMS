"""
Usage:
    python seed_data.py          # run after create_tables.py
    python seed_data.py --reset  # drop + recreate + reseed
"""

import sys
import random
from datetime import date, datetime, timedelta
from db.connection import get_connection

random.seed(42)  # reproducible data

# ═══════════════════════════════════════════════════════════════════════
# REFERENCE DATA
# ═══════════════════════════════════════════════════════════════════════

CUSTOMER_TYPES = [
    (1, "Residential",  "Individual household connections"),
    (2, "Commercial",   "Shops, malls, and business establishments"),
    (3, "Industrial",   "Factories and manufacturing units"),
    (4, "Agricultural", "Farms and irrigation pump connections"),
    (5, "Government",   "Government offices and public institutions"),
]

PIN_CODES = [
    # (pin,      city,          district,        state)
    ("380001", "Ahmedabad",    "Ahmedabad",      "GUJARAT"),
    ("382010", "Gandhinagar",  "Gandhinagar",     "GUJARAT"),
    ("395003", "Surat",        "Surat",           "GUJARAT"),
    ("360001", "Rajkot",       "Rajkot",          "GUJARAT"),
    ("400001", "Mumbai",       "Mumbai City",     "MAHARASHTRA"),
    ("411001", "Pune",         "Pune",            "MAHARASHTRA"),
    ("440010", "Nagpur",       "Nagpur",          "MAHARASHTRA"),
    ("302001", "Jaipur",       "Jaipur",          "RAJASTHAN"),
    ("313001", "Udaipur",      "Udaipur",         "RAJASTHAN"),
    ("342001", "Jodhpur",      "Jodhpur",         "RAJASTHAN"),
    ("462001", "Bhopal",       "Bhopal",          "MADHYA PRADESH"),
    ("452001", "Indore",       "Indore",          "MADHYA PRADESH"),
    ("560001", "Bengaluru",    "Bengaluru Urban", "KARNATAKA"),
    ("600001", "Chennai",      "Chennai",         "TAMIL NADU"),
    ("226001", "Lucknow",      "Lucknow",         "UTTAR PRADESH"),
    ("700001", "Kolkata",      "Kolkata",         "WEST BENGAL"),
]

# Substations: 12 across key pin codes
# Some pin codes get 2 substations; some get 1
SUBSTATIONS = [
    # (id,           area,                    voltage, capacity, transformer, breaker_type,  status,   pin)
    ("SUB0380001", "Maninagar",               132.00, 500.00, 450.00, "SF6",       "Active",   "380001"),
    ("SUB0380002", "Navrangpura",             66.00,  300.00, 280.00, "Vacuum",    "Active",   "380001"),
    ("SUB0382010", "Sector 21 Gandhinagar",   132.00, 400.00, 380.00, "SF6",       "Active",   "382010"),
    ("SUB0395003", "Adajan",                  66.00,  350.00, 320.00, "Oil",       "Active",   "395003"),
    ("SUB0400001", "Andheri",                 220.00, 800.00, 750.00, "SF6",       "Active",   "400001"),
    ("SUB0400002", "Bandra",                  132.00, 600.00, 550.00, "SF6",       "Active",   "400001"),
    ("SUB0411001", "Kothrud",                 66.00,  350.00, 320.00, "Vacuum",    "Active",   "411001"),
    ("SUB0302001", "Malviya Nagar",           132.00, 450.00, 420.00, "Oil",       "Active",   "302001"),
    ("SUB0560001", "Koramangala",             220.00, 700.00, 650.00, "SF6",       "Active",   "560001"),
    ("SUB0600001", "T. Nagar",               132.00, 500.00, 470.00, "Vacuum",    "Active",   "600001"),
    ("SUB0226001", "Gomti Nagar",             66.00,  300.00, 280.00, "Oil",       "Active",   "226001"),
    ("SUB0700001", "Salt Lake",              132.00, 450.00, 430.00, "SF6",       "Inactive", "700001"),
]

# Feeders: 42 total.  SUB0380001 and SUB0400001 each get 5+ (for query 18).
# Load_Profile is intentionally small on some feeders so query 10
# (overloaded feeders) triggers with a realistic number of meters.
FEEDERS = []
_feeder_plan = {
    "SUB0380001": [("Maninagar East",  11.00, 50.0, 0.008, 12.5, 0),
                   ("Maninagar West",  11.00, 45.0, 0.010, 12.5, 0),
                   ("Kankaria",        11.00, 40.0, 0.009, 12.5, 0),
                   ("Isanpur",         11.00, 35.0, 0.007, 12.5, 0),
                   ("Danilimda",       11.00, 30.0, 0.012, 12.5, 0)],
    "SUB0380002": [("Navrangpura Main",11.00, 40.0, 0.010, 12.5, 0),
                   ("Paldi",           11.00, 35.0, 0.008, 12.5, 0),
                   ("Ellis Bridge",    11.00, 30.0, 0.009, 12.5, 0)],
    "SUB0382010": [("Sector 7",        11.00, 45.0, 0.011, 12.5, 0),
                   ("Sector 15",       11.00, 40.0, 0.010, 12.5, 0),
                   ("Infocity",        11.00, 50.0, 0.009, 12.5, 0)],
    "SUB0395003": [("Adajan Patiya",   11.00, 40.0, 0.010, 12.5, 0),
                   ("Vesu",            11.00, 35.0, 0.008, 12.5, 0)],
    "SUB0400001": [("Andheri East",    11.00, 60.0, 0.009, 12.5, 0),
                   ("Andheri West",    11.00, 55.0, 0.011, 12.5, 0),
                   ("Jogeshwari",      11.00, 50.0, 0.010, 12.5, 0),
                   ("Goregaon",        11.00, 45.0, 0.008, 12.5, 0),
                   ("Malad",           11.00, 40.0, 0.012, 12.5, 0),
                   ("Kandivali",       11.00, 35.0, 0.007, 12.5, 0)],
    "SUB0400002": [("Bandra East",     11.00, 50.0, 0.010, 12.5, 0),
                   ("Bandra West",     11.00, 45.0, 0.009, 12.5, 0),
                   ("Khar",            11.00, 40.0, 0.011, 12.5, 0)],
    "SUB0411001": [("Kothrud Main",    11.00, 40.0, 0.010, 12.5, 0),
                   ("Karve Nagar",     11.00, 35.0, 0.009, 12.5, 0)],
    "SUB0302001": [("Malviya Nagar E", 11.00, 40.0, 0.010, 12.5, 0),
                   ("C-Scheme",        11.00, 45.0, 0.008, 12.5, 0),
                   ("Vaishali Nagar",  11.00, 35.0, 0.009, 12.5, 0)],
    "SUB0560001": [("Koramangala 4th", 11.00, 55.0, 0.010, 12.5, 0),
                   ("HSR Layout",      11.00, 50.0, 0.009, 12.5, 0),
                   ("Indiranagar",     11.00, 45.0, 0.011, 12.5, 0),
                   ("Jayanagar",       11.00, 40.0, 0.008, 12.5, 0)],
    "SUB0600001": [("T Nagar Main",    11.00, 50.0, 0.010, 12.5, 0),
                   ("Nungambakkam",    11.00, 45.0, 0.009, 12.5, 0),
                   ("Kodambakkam",     11.00, 40.0, 0.011, 12.5, 0)],
    "SUB0226001": [("Gomti Nagar Ext", 11.00, 35.0, 0.010, 12.5, 0),
                   ("Hazratganj",      11.00, 30.0, 0.009, 12.5, 0)],
    "SUB0700001": [("Salt Lake Sec V", 11.00, 40.0, 0.010, 12.5, 0),
                   ("New Town",        11.00, 35.0, 0.008, 12.5, 0)],
}

_fdr_seq = 1
for sub_id, feeders in _feeder_plan.items():
    for area, volt, cap, lp, cbr, nom in feeders:
        fdr_id = f"FDR{_fdr_seq:08d}"
        FEEDERS.append((fdr_id, area, volt, cap, lp, cbr, nom, sub_id))
        _fdr_seq += 1

# Build a lookup: substation_id -> pin_code
_sub_pin = {s[0]: s[7] for s in SUBSTATIONS}
# Build a lookup: feeder_id -> substation_id
_fdr_sub = {f[0]: f[7] for f in FEEDERS}

# ── Indian names for customers and employees ───────────────────────────
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav",
    "Advait", "Dhruv", "Kabir", "Ritvik", "Aarush", "Kayaan",
    "Ananya", "Diya", "Myra", "Sara", "Aadhya", "Ira", "Aanya", "Navya",
    "Prisha", "Kiara", "Riya", "Tara", "Meera", "Saanvi", "Pihu",
    "Nisha", "Pooja", "Sneha", "Kavya", "Lakshmi",
    "Rajesh", "Suresh", "Mahesh", "Ramesh", "Deepak", "Amit",
    "Sunita", "Rekha", "Geeta", "Suman", "Kiran", "Neha",
]
LAST_NAMES = [
    "Patel", "Shah", "Sharma", "Mehta", "Desai", "Joshi", "Gupta",
    "Singh", "Kumar", "Reddy", "Nair", "Iyer", "Rao", "Das",
    "Verma", "Pandey", "Chauhan", "Malhotra", "Thakur", "Chopra",
    "Agarwal", "Bhat", "Pillai", "Menon", "Hegde", "Patil",
]
STREETS = [
    "MG Road", "Station Road", "Gandhi Nagar", "Nehru Street",
    "Laxmi Chowk", "Sardar Patel Marg", "Ring Road", "Canal Road",
    "Industrial Area", "GIDC Road", "Market Yard Road", "Civil Lines",
    "Tilak Road", "Shastri Nagar", "Ambedkar Road", "Tagore Marg",
]


def _random_phone():
    return f"{random.randint(7000000000, 9999999999)}"


def _random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


# ═══════════════════════════════════════════════════════════════════════
# DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_customers(n=160):
    """
    160 customers spread across pin codes and customer types.
    ~70% Residential, ~15% Commercial, ~8% Industrial, ~5% Agricultural, ~2% Government.
    ~85% Connected, ~15% Disconnected.
    """
    rows = []
    weights = [0.70, 0.15, 0.08, 0.05, 0.02]
    type_ids = [1, 2, 3, 4, 5]
    used_phones = set()

    for i in range(1, n + 1):
        cid = f"CUST{i:08d}"
        name = _random_name()
        while True:
            phone = _random_phone()
            if phone not in used_phones:
                used_phones.add(phone)
                break
        pin = random.choice(PIN_CODES)[0]
        block = f"{random.choice('ABCDEFGH')}-{random.randint(1, 400)}"
        street = random.choice(STREETS)
        billing_cycle = random.choice([1, 2, 3])  # months
        status = "Connected" if random.random() < 0.85 else "Disconnected"
        ct_id = random.choices(type_ids, weights=weights, k=1)[0]
        rows.append((cid, name, phone, block, street, billing_cycle, status, ct_id, pin))
    return rows


def generate_meters(customers, feeders):
    """One meter per connected customer, assigned round-robin across feeders in their pin code."""
    rows = []
    # Group feeders by pin code
    pin_feeders = {}
    for f in feeders:
        fdr_id, _, _, _, _, _, _, sub_id = f
        pin = _sub_pin[sub_id]
        pin_feeders.setdefault(pin, []).append(fdr_id)

    all_feeder_ids = [f[0] for f in feeders]
    meter_seq = 1

    for c in customers:
        cid, _, _, _, _, _, conn_status, _, pin = c
        if conn_status == "Disconnected":
            continue
        # Pick a feeder in the customer's pin code; fall back to any feeder
        available = pin_feeders.get(pin, all_feeder_ids)
        fdr_id = available[meter_seq % len(available)]
        mid = f"MTR{meter_seq:09d}"
        install_date = date(random.randint(2016, 2021), random.randint(1, 12), random.randint(1, 28))
        last_read = date(2024, random.randint(1, 6), random.randint(1, 28))
        reading = round(random.uniform(500, 50000), 2)
        status = "Active" if random.random() < 0.92 else "Inactive"
        rows.append((mid, reading, status, install_date, last_read, fdr_id, cid))
        meter_seq += 1
    return rows


def generate_electricity_rates():
    """Multiple rate periods per customer type across 2017-2024."""
    rows = []
    rate_seq = 1
    periods = [
        (date(2017, 1, 1), date(2018, 12, 31)),
        (date(2019, 1, 1), date(2020, 12, 31)),
        (date(2021, 1, 1), date(2022, 12, 31)),
        (date(2023, 1, 1), date(2024, 6, 30)),
    ]
    # Base rate by customer type (₹/kWh)
    base_rates = {1: 4.50, 2: 7.00, 3: 6.00, 4: 3.50, 5: 5.50}

    for ct_id, base in base_rates.items():
        for i, (sd, ed) in enumerate(periods):
            rid = f"RATE{rate_seq:08d}"
            # Rates increase ~8% every period
            rate_val = round(base * (1.08 ** i), 2)
            rows.append((rid, sd, ed, rate_val, ct_id))
            rate_seq += 1
    return rows


def generate_bills(meters, rates):
    """
    Generate monthly bills for each meter across 2018-2024.
    ~80% Paid, ~20% Unpaid. Some bills > ₹1000 for query 17.
    """
    rows = []
    bill_seq = 1

    # Build a lookup: customer_type_id -> list of (rate_id, start, end, rate_val)
    # We need to find the customer type for each meter's customer.
    # For simplicity, assign rates round-robin from the rate list per period.
    # Group rates by customer_type_id
    rates_by_type = {}
    for rid, sd, ed, rv, ctid in rates:
        rates_by_type.setdefault(ctid, []).append((rid, sd, ed, rv))

    # We'll need customer -> type mapping; pass it via a global built during seeding
    # For now, generate bills using a simple approach: each meter gets 1 bill/month
    # and we pick the rate whose period covers the billing date.

    for meter in meters:
        mid = meter[0]
        install_date = meter[3]
        customer_id = meter[6]

        # Get customer type from the global customer data
        ct_id = _customer_type_map.get(customer_id, 1)
        type_rates = rates_by_type.get(ct_id, rates_by_type[1])

        # Generate bills from install year to 2024, one per quarter to keep volume reasonable
        start_year = max(install_date.year, 2018)
        for year in range(start_year, 2025):
            for month in [2, 5, 8, 11]:  # quarterly billing
                billing_date = date(year, month, 15)
                if billing_date > date(2024, 6, 15):
                    break
                # Find applicable rate
                applicable_rate = type_rates[0]  # fallback
                for rid, sd, ed, rv in type_rates:
                    if sd <= billing_date <= ed:
                        applicable_rate = (rid, sd, ed, rv)
                        break

                # Generate a realistic bill amount
                # Residential: ₹200-2500, Commercial: ₹500-8000,
                # Industrial: ₹2000-25000, Agricultural: ₹100-1500, Government: ₹300-5000
                ranges = {1: (200, 2500), 2: (500, 8000), 3: (2000, 25000),
                          4: (100, 1500), 5: (300, 5000)}
                lo, hi = ranges.get(ct_id, (200, 2500))
                total_price = round(random.uniform(lo, hi), 2)

                payment = "Paid" if random.random() < 0.80 else "Unpaid"
                bid = f"BILL{bill_seq:012d}"
                rows.append((bid, total_price, billing_date, payment, mid, applicable_rate[0]))
                bill_seq += 1

    return rows


def generate_power_source_owners():
    return [
        ("TPC", "Tata Power Company",        "101", "Nariman Point",    "9876543210", "Thermal and Solar",    "400001"),
        ("AEL", "Adani Energy Ltd",           "202", "Shantigram",       "9876543211", "Solar and Wind",       "382010"),
        ("REL", "Reliance Energy Ltd",        "303", "BKC Complex",      "9876543212", "Thermal",              "400001"),
        ("NTP", "NTPC Gujarat",               "404", "Gandhinagar Main", "9876543213", "Thermal and Hydro",    "382010"),
        ("GEB", "Gujarat Energy Board",       "505", "Ashram Road",      "9876543214", "Hydro and Wind",       "380001"),
        ("SZN", "Suzlon Energy",              "606", "Hadapsar",         "9876543215", "Wind",                 "411001"),
    ]


def generate_power_sources():
    return [
        # (id,      type,      cap,    area,             gen,     status,  pin,      sub,          owner)
        ("THM001", "Thermal", 200.00, "Wanakbori",      180.00, "Active",  "380001", "SUB0380001", "TPC"),
        ("THM002", "Thermal", 500.00, "Mundra",         470.00, "Active",  "382010", "SUB0382010", "AEL"),
        ("SOL001", "Solar",   100.00, "Charanka",       85.00,  "Active",  "382010", "SUB0382010", "AEL"),
        ("SOL002", "Solar",    50.00, "Kamuthi",        42.00,  "Active",  "600001", "SUB0600001", "TPC"),
        ("WND001", "Wind",     80.00, "Jaisalmer",      65.00,  "Active",  "302001", "SUB0302001", "SZN"),
        ("WND002", "Wind",     60.00, "Kutch",          52.00,  "Active",  "380001", "SUB0380002", "GEB"),
        ("HYD001", "Hydro",   150.00, "Sardar Sarovar", 130.00, "Active",  "395003", "SUB0395003", "NTP"),
        ("HYD002", "Hydro",   120.00, "Koyna",          105.00, "Active",  "411001", "SUB0411001", "NTP"),
        ("THM003", "Thermal", 300.00, "Trombay",        280.00, "Active",  "400001", "SUB0400001", "REL"),
        ("SOL003", "Solar",    75.00, "Anantapur",       60.00, "Active",  "560001", "SUB0560001", "AEL"),
        ("WND003", "Wind",     40.00, "Tirunelveli",     32.00, "Inactive","600001", "SUB0600001", "SZN"),
        ("THM004", "Thermal", 250.00, "Korba",          230.00, "Active",  "462001", "SUB0226001", "NTP"),
    ]


def generate_maintenance_teams():
    return [
        ("TEAM0001", "Electrical Repair"),
        ("TEAM0002", "Transformer Maintenance"),
        ("TEAM0003", "Line Inspection"),
        ("TEAM0004", "Emergency Response"),
        ("TEAM0005", "Meter Calibration"),
        ("TEAM0006", "Vegetation Management"),
        ("TEAM0007", "Electrical Repair"),
        ("TEAM0008", "Substation Overhaul"),
    ]


def generate_maintenance_schedules():
    """25 maintenance schedules across substations and teams."""
    rows = []
    ms_seq = 1
    sub_ids = [s[0] for s in SUBSTATIONS]
    team_ids = [t[0] for t in generate_maintenance_teams()]
    m_types = ["Preventive", "Corrective", "Emergency", "Inspection", "Upgrade"]

    base = datetime(2019, 1, 10, 8, 0, 0)
    for i in range(25):
        mid = f"MAINT{ms_seq:06d}"
        start = base + timedelta(days=i * 15, hours=random.randint(0, 8))
        end = start + timedelta(hours=random.randint(2, 48))
        mtype = random.choice(m_types)
        status = random.choice(["Scheduled", "Completed", "Completed", "Completed", "Cancelled"])
        sub_id = sub_ids[i % len(sub_ids)]
        team_id = team_ids[i % len(team_ids)]
        rows.append((mid, start, end, mtype, status, sub_id, team_id))
        ms_seq += 1
    return rows


def generate_outages(maintenance_schedules):
    """
    20 outages linked to maintenance schedules.
    Concentrated in certain pin codes so query 12 (>10 outages) fires.
    Include outages in 2020 specifically for query 34.
    """
    rows = []
    out_seq = 1
    causes = [
        "Equipment failure", "Storm damage", "Overloaded transformer",
        "Cable fault", "Tree fall on line", "Scheduled upgrade",
        "Lightning strike", "Flooding", "Planned maintenance",
        "Animal interference",
    ]
    for i, ms in enumerate(maintenance_schedules[:20]):
        oid = f"OUT{out_seq:09d}"
        start = ms[1] + timedelta(hours=random.randint(0, 2))
        end = ms[2] + timedelta(hours=random.randint(0, 4))
        status = random.choice(["Scheduled", "Ongoing", "Resolved", "Resolved", "Resolved"])
        otype = "Scheduled" if "Planned" in (ms[3] or "") or "Scheduled" in (ms[3] or "") else random.choice(["Scheduled", "Unexpected", "Unexpected"])
        cause = random.choice(causes)
        rows.append((oid, start, end, status, otype, cause, ms[0]))
        out_seq += 1
    return rows


def generate_affected_areas(outages):
    """
    Multiple affected areas per outage.
    Pin code 380001 gets the most outage hits (for query 12 threshold).
    """
    rows = []
    aa_seq = 1
    area_types = ["Residential", "Commercial", "Industrial", "Mixed"]
    # Distribute: first 8 outages hit 380001 heavily
    heavy_pin = "380001"
    heavy_areas = ["Maninagar", "Kankaria", "Isanpur", "Danilimda", "Rakhial"]

    for i, outage in enumerate(outages):
        oid = outage[0]
        # Each outage affects 1-3 areas
        n_areas = random.randint(1, 3)
        for j in range(n_areas):
            aaid = f"AA{aa_seq:010d}"
            if i < 8:  # First 8 outages heavily hit 380001
                pin = heavy_pin
                area = heavy_areas[j % len(heavy_areas)]
            else:
                pin = random.choice(PIN_CODES)[0]
                area = f"Area-{random.randint(1, 50)}"
            atype = random.choice(area_types)
            rows.append((aaid, atype, area, pin, oid))
            aa_seq += 1
    return rows


def generate_employees():
    """
    45 employees. Some substations get 2+ Managers (for query 31).
    """
    rows = []
    emp_seq = 1
    roles = ["Manager", "Technician", "Engineer", "Supervisor", "Lineman", "Operator"]
    departments = ["Operations", "Maintenance", "Planning", "Safety", "Administration"]
    sub_ids = [s[0] for s in SUBSTATIONS]
    team_ids = [t[0] for t in generate_maintenance_teams()]
    used_phones = set()

    for i in range(45):
        eid = f"EMP{emp_seq:05d}"
        name = _random_name()
        # First 2 substations get 2 Managers each (for query 31)
        if i < 2:
            role = "Manager"
            sub_id = "SUB0380001"
        elif i < 4:
            role = "Manager"
            sub_id = "SUB0400001"
        else:
            role = random.choice(roles)
            sub_id = random.choice(sub_ids)
        dept = random.choice(departments)
        salary = round(random.uniform(25000, 120000), 2)
        while True:
            phone = _random_phone()
            if phone not in used_phones:
                used_phones.add(phone)
                break
        team_id = random.choice(team_ids)
        rows.append((eid, name, role, dept, salary, phone, sub_id, team_id))
        emp_seq += 1
    return rows


def generate_substation_connections():
    """Connections between nearby substations."""
    return [
        ("SUB0380001", "SUB0380002"),
        ("SUB0380001", "SUB0382010"),
        ("SUB0380002", "SUB0382010"),
        ("SUB0400001", "SUB0400002"),
        ("SUB0400001", "SUB0411001"),
        ("SUB0560001", "SUB0600001"),
        ("SUB0302001", "SUB0226001"),
        ("SUB0382010", "SUB0395003"),
        ("SUB0395003", "SUB0400001"),
        ("SUB0700001", "SUB0226001"),
    ]


# ═══════════════════════════════════════════════════════════════════════
# INSERT HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _insert_many(cur, table, columns, rows):
    """Parameterized bulk insert."""
    if not rows:
        return
    placeholders = ", ".join(["%s"] * len(columns))
    cols = ", ".join(columns)
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    cur.executemany(sql, rows)
    print(f"  ✓ {table}: {len(rows)} rows")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

# Global map built during generation so bills can look up customer types
_customer_type_map = {}


def main():
    global _customer_type_map

    if "--reset" in sys.argv:
        print("Resetting database ...")
        conn = get_connection()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP SCHEMA IF EXISTS electricity_grid_management CASCADE;")
        cur.close()
        conn.close()
        # Re-create tables
        import create_tables
        create_tables.main()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SET search_path TO electricity_grid_management;")

    print("Seeding data ...\n")

    # 1. Customer_Type
    _insert_many(cur, "Customer_Type",
                 ["Customer_Type_ID", "Type_Name", "Description"],
                 CUSTOMER_TYPES)

    # 2. Pin_Code
    _insert_many(cur, "Pin_Code",
                 ["Pin_Code", "City", "District", "State"],
                 PIN_CODES)

    # 3. Customers
    customers = generate_customers(160)
    _customer_type_map = {c[0]: c[7] for c in customers}
    _insert_many(cur, "Customer",
                 ["Customer_ID", "Customer_Name", "Phone_Number",
                  "Block_Flat_No", "Street", "Billing_Cycle",
                  "Connection_Status", "Customer_Type_ID", "Pin_Code"],
                 customers)

    # 4. Substations
    _insert_many(cur, "Substation",
                 ["Substation_ID", "Area", "Voltage_Level", "Capacity",
                  "Transformer_Capacity", "Circuit_Breakers", "Status", "Pin_Code"],
                 SUBSTATIONS)

    # 5. Feeders
    _insert_many(cur, "Feeder",
                 ["Feeder_ID", "Area_Name", "Voltage_Level", "Capacity",
                  "Load_Profile", "Circuit_Breaker_Rating", "Number_Of_Meters",
                  "Substation_ID"],
                 FEEDERS)

    # 6. Meters
    meters = generate_meters(customers, FEEDERS)
    _insert_many(cur, "Meter",
                 ["Meter_ID", "Current_Reading", "Status", "Installation_Date",
                  "Last_Reading_Date", "Feeder_ID", "Customer_ID"],
                 meters)

    # 7. Electricity_Rate
    rates = generate_electricity_rates()
    _insert_many(cur, "Electricity_Rate",
                 ["Rate_ID", "Rate_Start_Date", "Rate_End_Date",
                  "Electricity_Rate", "Customer_Type_ID"],
                 rates)

    # 8. Bills
    bills = generate_bills(meters, rates)
    _insert_many(cur, "Bill",
                 ["Bill_ID", "Total_Price", "Billing_Date", "Payment_Status",
                  "Meter_ID", "Rate_ID"],
                 bills)

    # 9. Power_Source_Owner
    owners = generate_power_source_owners()
    _insert_many(cur, "Power_Source_Owner",
                 ["Owner_ID", "Name", "Office_No", "Street", "Contact_Info",
                  "Power_Source_Ownership_Details", "Pin_Code"],
                 owners)

    # 10. Power_Source
    sources = generate_power_sources()
    _insert_many(cur, "Power_Source",
                 ["Power_Source_ID", "Type", "Capacity", "Area",
                  "Generation_Data", "Status", "Pin_Code",
                  "Substation_ID", "Owner_ID"],
                 sources)

    # 11. Maintenance_Team
    teams = generate_maintenance_teams()
    _insert_many(cur, "Maintenance_Team",
                 ["Team_ID", "Team_Type"],
                 teams)

    # 12. Maintenance_Schedule
    schedules = generate_maintenance_schedules()
    _insert_many(cur, "Maintenance_Schedule",
                 ["Maintenance_ID", "Start_Date_Time", "End_Date_Time",
                  "Maintenance_Type", "Status", "Substation_ID", "Team_ID"],
                 schedules)

    # 13. Outages
    outages = generate_outages(schedules)
    _insert_many(cur, "Outage",
                 ["Outage_ID", "Start_Date_Time", "End_Date_Time",
                  "Status", "Outage_Type", "Cause", "Maintenance_ID"],
                 outages)

    # 14. Affected_Area
    affected = generate_affected_areas(outages)
    _insert_many(cur, "Affected_Area",
                 ["Affected_Area_ID", "Area_Type", "Area", "Pin_Code", "Outage_ID"],
                 affected)

    # 15. Employees
    employees = generate_employees()
    _insert_many(cur, "Employee",
                 ["Employee_ID", "Employee_Name", "Role", "Department",
                  "Salary", "Contact_Info", "Substation_ID", "Team_ID"],
                 employees)

    # 16. Substation_Connections
    connections = generate_substation_connections()
    _insert_many(cur, "Substation_Connections",
                 ["Substation1_ID", "Substation2_ID"],
                 connections)

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n{'='*50}")
    print(f"Seeding complete!")
    print(f"  Customers : {len(customers)}")
    print(f"  Meters    : {len(meters)}")
    print(f"  Bills     : {len(bills)}")
    print(f"  Outages   : {len(outages)}")
    print(f"  Employees : {len(employees)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()