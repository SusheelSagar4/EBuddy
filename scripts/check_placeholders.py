import os
import csv
import psycopg

total_placeholders = 0

try:
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
except Exception as e:
    print(f'PostgreSQL not connected ({e}). Auditing seed CSV files in data/seed/kb/:')
    seed_kb = os.path.join(os.path.dirname(__file__), "..", "data", "seed", "kb")
    for fn in os.listdir(seed_kb):
        if fn.endswith('.csv'):
            fp = os.path.join(seed_kb, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                cnt = 0
                for r in reader:
                    if r.get('is_placeholder', '').lower() == 'true':
                        cnt += 1
                if cnt > 0:
                    print(f'{fn} with is_placeholder=true: {cnt}')
                total_placeholders += cnt
    print(f'\nTotal is_placeholder=true rows across seed files: {total_placeholders}')

