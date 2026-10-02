import sqlite3
import pandas as pd
import os

excel_path = 'c:/Users/USER/Desktop/CHF JOINED DATA/member_data_cleaned_final.xlsx'
db_path = 'c:/Users/USER/Desktop/CHF JOINED DATA/backend/database.db'

print('Loading Excel...')
try:
    df = pd.read_excel(excel_path, engine='calamine')
except Exception:
    df = pd.read_excel(excel_path)

print('Cleaning data...')
df = df.astype(object).fillna('')
for col in df.columns:
    df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)

if '_search_col' not in df.columns:
    df['_search_col'] = df[df.columns[0]].str.cat(df[df.columns[1:]], sep=' ').str.lower()

print('Writing to SQLite safely...')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS members')

columns_def = ['_id INTEGER PRIMARY KEY AUTOINCREMENT']
for col in df.columns:
    if col != '_id':
        columns_def.append(f'"{col}" TEXT')
        
c.execute(f'CREATE TABLE members ({", ".join(columns_def)})')

# Insert data
df.to_sql('members', conn, if_exists='append', index=False)
conn.commit()
conn.close()

print('Done!')
