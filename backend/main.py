import psycopg2
import psycopg2.extras
import pandas as pd
import math
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sqlalchemy import create_engine

app = Flask(__name__)
CORS(app)

# Use Render environment variable for DB, fallback to Neon connection string
DB_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_HAOrfQjd8Ke1@ep-young-haze-b5krg0wi-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

def get_db():
    conn = psycopg2.connect(DB_URL)
    return conn

@app.route("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return jsonify({"status": "Backend is running, but frontend not found."})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if username == "prosper.kashaga" and password == "Ruthmsechu@822":
        return jsonify({"status": "success", "token": "fake-jwt-123"})
    else:
        return jsonify({"status": "error", "detail": "Jina au Password sio sahihi"}), 401

@app.route("/api/members", methods=["GET"])
def search_members():
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))
    
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    where_clause = ""
    params = []
    
    if query:
        where_clause = "WHERE _search_col LIKE %s"
        params.append(f"%{query.lower()}%")
        
    c.execute(f"SELECT COUNT(*) as cnt FROM members {where_clause}", params)
    total_records = c.fetchone()['cnt']
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
    
    offset = (page - 1) * page_size
    
    query_sql = f"SELECT * FROM members {where_clause} ORDER BY _id DESC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    
    c.execute(query_sql, params)
    rows = c.fetchall()
    
    records = []
    for row in rows:
        r = dict(row)
        r.pop('_search_col', None)
        records.append(r)
        
    conn.close()
    
    return jsonify({
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "data": records
    })

@app.route("/api/members", methods=["POST"])
def add_member():
    member = request.json
    conn = get_db()
    c = conn.cursor()
    
    cols = []
    vals = []
    search_parts = []
    
    for key, value in member.items():
        if key not in ('_search_col', '_id', 'index'):
            cols.append(f'"{key}"')
            val_str = str(value)
            vals.append(val_str)
            search_parts.append(val_str)
            
    search_col = " ".join(search_parts).lower()
    cols.append('"_search_col"')
    vals.append(search_col)
    
    placeholders = ",".join(["%s"] * len(vals))
    col_str = ",".join(cols)
    
    c.execute(f"INSERT INTO members ({col_str}) VALUES ({placeholders})", vals)
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Member added successfully"})

@app.route("/api/members/<int:member_id>", methods=["PUT"])
def edit_member(member_id):
    member = request.json
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    c.execute("SELECT * FROM members WHERE _id = %s", (member_id,))
    old_row = c.fetchone()
    if not old_row:
        conn.close()
        return jsonify({"detail": "Member not found"}), 404
        
    old_dict = dict(old_row)
    
    cols = []
    vals = []
    search_parts = []
    
    for key in old_dict.keys():
        if key not in ('_search_col', '_id', 'index'):
            cols.append(f'"{key}"')
            
            if key in member:
                val_str = str(member[key])
            else:
                val_str = str(old_dict[key])
                
            vals.append(val_str)
            search_parts.append(val_str)
            
    search_col = " ".join(search_parts).lower()
    cols.append('"_search_col"')
    vals.append(search_col)
    
    placeholders = ",".join(["%s"] * len(vals))
    col_str = ",".join(cols)
    
    # We insert it as a new row
    c.execute(f"INSERT INTO members ({col_str}) VALUES ({placeholders})", vals)
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Member edited and added as a new record successfully"})

@app.route("/api/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM members WHERE _id = %s", (member_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Member deleted successfully"})

@app.route("/api/upload", methods=["POST"])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"detail": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"detail": "No selected file"}), 400
        
    try:
        temp_file = "temp_uploaded.xlsx"
        file.save(temp_file)
            
        try:
            new_df = pd.read_excel(temp_file, engine='calamine')
        except Exception:
            new_df = pd.read_excel(temp_file)
            
        new_df = new_df.astype(object).fillna("")
        for col in new_df.columns:
            new_df[col] = new_df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(' 00:00:00', '', regex=False)
            
        if '_search_col' not in new_df.columns:
            new_df['_search_col'] = new_df[new_df.columns[0]].str.cat(new_df[new_df.columns[1:]], sep=' ').str.lower()
            
        # Write to Postgres
        # We need SQLAlchemy engine for pandas to_sql
        engine = create_engine(DB_URL.replace("postgres://", "postgresql://").replace("postgresql://", "postgresql+psycopg2://"))
        
        # We don't include _id column if it's missing, PostgreSQL SERIAL will handle it.
        # However, to_sql replaces by default if we don't specify if_exists='append'
        new_df.to_sql('members', engine, if_exists='append', index=False, chunksize=1000)
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        return jsonify({"status": "success", "message": f"{len(new_df)} members uploaded successfully!"})
    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({"detail": str(e)}), 500

@app.route("/api/template", methods=["GET"])
def download_template():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("SELECT * FROM members LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"detail": "No columns found"}), 404
        
    cols = [key for key in dict(row).keys() if key not in ('_id', 'index', '_search_col')]
    
    template_df = pd.DataFrame(columns=cols)
    temp_file = "template.xlsx"
    template_df.to_excel(temp_file, index=False, engine='openpyxl')
    return send_file(temp_file, as_attachment=True, download_name="Member_Template.xlsx")

@app.route("/api/download", methods=["GET"])
def download_excel():
    query = request.args.get("query", "")
    
    where_clause = ""
    params = []
    
    if query:
        where_clause = "WHERE _search_col LIKE %s"
        params.append(f"%{query.lower()}%")
        
    # Pandas read_sql_query supports SQLAlchemy engines, which is safer
    engine = create_engine(DB_URL.replace("postgres://", "postgresql://").replace("postgresql://", "postgresql+psycopg2://"))
    df = pd.read_sql_query(f"SELECT * FROM members {where_clause}", engine, params=params)
    
    cols_to_drop = [c for c in ['_id', 'index', '_search_col'] if c in df.columns]
    df = df.drop(columns=cols_to_drop)
    
    temp_file = "filtered_results.xlsx"
    df.to_excel(temp_file, index=False, engine='openpyxl')
    
    return send_file(temp_file, as_attachment=True, download_name="members_search_results.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(port=8000, debug=True)
