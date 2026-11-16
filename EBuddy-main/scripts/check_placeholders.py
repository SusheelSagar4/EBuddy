import psycopg

conn = psycopg.connect('postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy', connect_timeout=3)
cur = conn.cursor()

# Find all tables with column is_placeholder
cur.execute('''
    SELECT table_schema, table_name 
    FROM information_schema.columns 
    WHERE column_name = 'is_placeholder'
    ORDER BY table_schema, table_name;
''')
cols = cur.fetchall()
print('Tables with is_placeholder column:', cols)

total_placeholders = 0
for s, t in cols:
    cur.execute(f'SELECT count(*) FROM {s}."{t}" WHERE is_placeholder = true;')
    cnt = cur.fetchone()[0]
    total_placeholders += cnt
    print(f'{s}.{t} with is_placeholder=true: {cnt}')
    if cnt > 0:
        cur.execute(f'SELECT * FROM {s}."{t}" WHERE is_placeholder = true;')
        col_names = [d[0] for d in cur.description]
        print('  Columns:', col_names)
        for row in cur.fetchall():
            print('  Row:', row)

print(f'\nTotal is_placeholder=true rows across all tables: {total_placeholders}')
conn.close()

