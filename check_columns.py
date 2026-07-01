#!/usr/bin/env python
"""Check actual columns in production database"""
import os
import psycopg2

# Connect directly to production database
conn = psycopg2.connect(
    "postgresql://postgres:HogFaJuzRvZXMXIfRTmSInWAxIenfYCG@ballast.proxy.rlwy.net:35095/railway"
)

cur = conn.cursor()

# Get columns for admindashboardfeatures table
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'hospital_admindashboardfeatures'
    ORDER BY ordinal_position;
""")

print("=== Columns in hospital_admindashboardfeatures ===")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[0]} ({col[1]})")

cur.close()
conn.close()