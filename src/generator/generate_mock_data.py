"""
Synthetic Indonesian E-Commerce & Customer Data Generator.
Produces 100% fake, realistic data for compliance testing under UU PDP.
"""

import random
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from faker import Faker
import pandas as pd
from src.config import RAW_DB_PATH

# Initialize Faker with Indonesian locale
fake = Faker("id_ID")
random.seed(42)
Faker.seed(42)

# Indonesian Province Codes (Kode Wilayah BPS/Kemendagri)
VALID_PROVINCES = [
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21,  # Sumatera
    31, 32, 33, 34, 35, 36,                  # Jawa
    51, 52, 53,                              # Bali & Nusa Tenggara
    61, 62, 63, 64, 65,                      # Kalimantan
    71, 72, 73, 74, 75, 76,                  # Sulawesi
    81, 82, 91, 94                           # Maluku & Papua
]


def generate_indonesian_nik(gender: str = "random", birth_date: datetime = None) -> str:
    """
    Generates a realistic 16-digit Indonesian NIK:
    - 2 digits: Province code
    - 2 digits: Regency / City code (01 - 79)
    - 2 digits: District code (01 - 25)
    - 6 digits: Birth date (DDMMYY). If female, DD = Day + 40.
    - 4 digits: Serial number (0001 - 0999)
    """
    prov = random.choice(VALID_PROVINCES)
    city = random.randint(1, 79)
    subdistrict = random.randint(1, 25)

    if not birth_date:
        days_ago = random.randint(18 * 365, 65 * 365)
        birth_date = datetime.now() - timedelta(days=days_ago)

    day = birth_date.day
    month = birth_date.month
    year_yy = birth_date.year % 100

    if gender == "random":
        is_female = random.choice([True, False])
    else:
        is_female = gender.lower() in ["f", "female", "perempuan", "wanita"]

    if is_female:
        day += 40

    serial = random.randint(1, 999)
    return f"{prov:02d}{city:02d}{subdistrict:02d}{day:02d}{month:02d}{year_yy:02d}{serial:04d}"


def generate_indonesian_npwp() -> str:
    """Generates an Indonesian NPWP formatted as XX.XXX.XXX.X-XXX.XXX"""
    p1 = random.randint(1, 99)
    p2 = random.randint(100, 999)
    p3 = random.randint(100, 999)
    p4 = random.randint(1, 9)
    p5 = random.randint(100, 999)
    p6 = random.randint(1, 999)
    return f"{p1:02d}.{p2:03d}.{p3:03d}.{p4:01d}-{p5:03d}.{p6:03d}"


def generate_indonesian_phone() -> str:
    """Generates Indonesian mobile numbers (+62 or 08xx)"""
    prefixes = ["0812", "0813", "0821", "0852", "0853", "0857", "0858", "0877", "0878", "0896"]
    prefix = random.choice(prefixes)
    # Choose between international +62 or domestic 08
    if random.random() < 0.3:
        prefix = "+62" + prefix[1:]
    suffix = "".join([str(random.randint(0, 9)) for _ in range(random.randint(7, 8))])
    return f"{prefix}{suffix}"


def generate_mock_dataset(num_customers: int = 1000, num_orders: int = 3000):
    """Generates customer and order datasets with realistic Indonesian PII attributes."""
    print(f"[*] Generating {num_customers} synthetic customer records...")

    customers = []
    customer_ids = []

    for _ in range(num_customers):
        cust_id = str(uuid.uuid4())
        customer_ids.append(cust_id)
        
        # Gender & Name
        is_female = random.choice([True, False])
        first_name = fake.first_name_female() if is_female else fake.first_name_male()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        
        # Birth Date
        days_ago = random.randint(18 * 365, 60 * 365)
        birth_dt = datetime.now() - timedelta(days=days_ago)
        
        # PII Attributes
        nik = generate_indonesian_nik(gender="f" if is_female else "m", birth_date=birth_dt)
        npwp = generate_indonesian_npwp()
        phone = generate_indonesian_phone()
        email = f"{first_name.lower()}.{last_name.lower().replace(' ', '')}{random.randint(10, 99)}@{fake.free_email_domain()}"
        address = fake.address().replace("\n", ", ")
        income = random.randint(5, 50) * 1_000_000 # 5M - 50M IDR

        customers.append({
            "customer_id": cust_id,
            "full_name": full_name,
            "nik": nik,
            "npwp": npwp,
            "phone_number": phone,
            "email": email,
            "birth_date": birth_dt.strftime("%Y-%m-%d"),
            "residential_address": address,
            "monthly_income_idr": income,
            "risk_score": round(random.uniform(0.1, 0.9), 2),
            "created_at": (datetime.now() - timedelta(days=random.randint(30, 700))).isoformat()
        })

    df_customers = pd.DataFrame(customers)

    print(f"[*] Generating {num_orders} synthetic order transactions...")
    orders = []
    payment_methods = ["BCA Virtual Account", "Mandiri Livin", "GoPay", "OVO", "ShopeePay", "Credit Card VISA"]

    for _ in range(num_orders):
        order_id = f"INV-{datetime.now().strftime('%Y%m')}-{random.randint(100000, 999999)}"
        cust_id = random.choice(customer_ids)
        cust_info = df_customers[df_customers["customer_id"] == cust_id].iloc[0]
        
        # 80% shipping matches customer address, 20% different
        ship_addr = cust_info["residential_address"] if random.random() < 0.8 else fake.address().replace("\n", ", ")
        ship_phone = cust_info["phone_number"] if random.random() < 0.8 else generate_indonesian_phone()

        orders.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "recipient_name": cust_info["full_name"],
            "recipient_phone": ship_phone,
            "shipping_address": ship_addr,
            "payment_method": random.choice(payment_methods),
            "order_amount_idr": random.randint(50, 5000) * 1000,
            "order_status": random.choice(["COMPLETED", "COMPLETED", "COMPLETED", "REFUNDED", "CANCELLED"]),
            "order_timestamp": (datetime.now() - timedelta(days=random.randint(1, 180), minutes=random.randint(0, 1440))).isoformat()
        })

    df_orders = pd.DataFrame(orders)

    # Persist to SQLite
    RAW_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(RAW_DB_PATH)
    df_customers.to_sql("customers_raw", conn, if_exists="replace", index=False)
    df_orders.to_sql("orders_raw", conn, if_exists="replace", index=False)
    conn.close()

    # Also save CSV exports for quick inspections
    csv_cust_path = RAW_DB_PATH.parent / "customers_raw.csv"
    csv_orders_path = RAW_DB_PATH.parent / "orders_raw.csv"
    df_customers.to_csv(csv_cust_path, index=False)
    df_orders.to_csv(csv_orders_path, index=False)

    print(f"[+] Successfully generated and stored raw data in {RAW_DB_PATH}!")
    print(f"[+] Customers: {len(df_customers)} rows, Orders: {len(df_orders)} rows.")
    return df_customers, df_orders


if __name__ == "__main__":
    generate_mock_dataset(num_customers=500, num_orders=1500)
