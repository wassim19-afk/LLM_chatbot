from data.db_connection import execute_query

tables = ["Fact_Purshase", "Fact_VendorPayementDetail"]

for table in tables:
    print(f"\n{table}\n" + "=" * 70)
    rows = execute_query(
        f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='{table}'
        ORDER BY ORDINAL_POSITION
        """
    )
    if not rows:
        print("Not found")
        continue
    for row in rows:
        print(f"{row['COLUMN_NAME']} ({row['DATA_TYPE']})")
