from data.db_connection import get_db_connection

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    
    print('\n📋 ALL TABLES IN DATABASE:')
    print('='*60)
    tables = cursor.fetchall()
    for schema, table in tables:
        print(f'{schema}.{table}')
    
    # Get columns for fact tables
    print('\n\n📊 COLUMNS IN FACT TABLES:')
    print('='*60)
    
    fact_tables = [
        'Fact_CustomerPayementDetail',
        'Fact_PurchaseDetail', 
        'Fact_CashInDetail',
        'Fact_CashOutDetail',
        'Fact_Sales',
        'Fact_Revenue'
    ]
    
    for table_name in fact_tables:
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        cols = cursor.fetchall()
        if cols:
            print(f'\n✅ {table_name}:')
            for col_name, col_type in cols:
                print(f'   - [{col_name}] ({col_type})')
        else:
            print(f'\n❌ {table_name} not found')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {str(e)}')
