from fastapi import FastAPI, Query, Body, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import math
import os

app = FastAPI()

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'member_data_cleaned_final.xlsx')

def load_data():
    print(f"Loading data from {DATA_FILE_PATH}...")
    try:
        try:
            df = pd.read_excel(DATA_FILE_PATH, engine='calamine')
        except Exception:
            df = pd.read_excel(DATA_FILE_PATH)
            
        # Convert to object to allow empty strings, then fillna
        df = df.astype(object).fillna("")
        
        # Super fast vectorized cleaning
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(' 00:00:00', '', regex=False)
            
        df['_search_col'] = df[df.columns[0]].str.cat(df[df.columns[1:]], sep=' ').str.lower()
        print("Data loaded successfully.")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

def save_data():
    global df
    print("Saving data to excel safely...")
    export_df = df.drop(columns=['_search_col'])
    
    temp_path = DATA_FILE_PATH.replace('.xlsx', '_temp.xlsx')
    export_df.to_excel(temp_path, index=False, engine='openpyxl')
    
    if os.path.exists(DATA_FILE_PATH):
        backup_path = DATA_FILE_PATH.replace('.xlsx', '_backup.xlsx')
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(DATA_FILE_PATH, backup_path)
        
    os.rename(temp_path, DATA_FILE_PATH)
    print("Data saved.")

@app.get("/")
def index():
    return {"status": "Backend is running"}

@app.get("/reload")
def reload_excel_data():
    global df
    df = load_data()
    return {"status": "success", "message": "Data reloaded successfully from Excel!"}

@app.get("/members")
def search_members(
    query: str = Query("", description="Search term across all columns"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000)
):
    if df.empty:
        return {"error": "Data file not found or empty"}

    filtered_df = df
    if query:
        # Use the optimized search column
        mask = filtered_df['_search_col'].str.contains(query.lower(), na=False)
        filtered_df = filtered_df[mask]
    
    total_records = len(filtered_df)
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
    
    # Pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_df = filtered_df.iloc[start_idx:end_idx].copy()
    paginated_df['_id'] = paginated_df.index # Give frontend the true row index
    paginated_df = paginated_df.drop(columns=['_search_col'])
    
    records = paginated_df.to_dict(orient="records")
    
    return {
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "data": records
    }

@app.post("/members")
def add_member(member: dict = Body(...)):
    global df
    new_idx = len(df)
    
    new_row = {}
    for col in df.columns:
        if col != '_search_col':
            new_row[col] = str(member.get(col, ""))
            
    df.loc[new_idx] = new_row
    df.at[new_idx, '_search_col'] = ' '.join(df.loc[new_idx].drop('_search_col').values).lower()
    
    save_data()
    return {"status": "success", "message": "Member added successfully"}

@app.put("/members/{member_id}")
def edit_member(member_id: int, member: dict = Body(...)):
    global df
    if member_id not in df.index:
        raise HTTPException(status_code=404, detail="Member not found")
        
    old_row = df.loc[member_id].to_dict()
    new_idx = len(df)
    
    new_row = {}
    for col in df.columns:
        if col != '_search_col':
            if col in member:
                new_row[col] = str(member[col])
            else:
                new_row[col] = old_row.get(col, "")
                
    # Add as a new record at the bottom
    df.loc[new_idx] = new_row
    
    # Re-calculate search column for the new row
    df.at[new_idx, '_search_col'] = ' '.join(df.loc[new_idx].drop('_search_col').values).lower()
    
    save_data()
    return {"status": "success", "message": "Member edited and added as a new record successfully"}

@app.delete("/members/{member_id}")
def delete_member(member_id: int):
    global df
    if member_id not in df.index:
        return {"status": "success", "message": "Member already deleted"}
        
    df.drop(index=member_id, inplace=True)
    save_data()
    return {"status": "success", "message": "Member deleted successfully"}

@app.post("/upload")
def upload_excel(file: UploadFile = File(...)):
    global df
    try:
        # Save uploaded file to temp
        temp_file = "temp_uploaded.xlsx"
        with open(temp_file, "wb") as f:
            f.write(file.file.read())
            
        # Read the new data
        try:
            new_df = pd.read_excel(temp_file, engine='calamine')
        except Exception:
            new_df = pd.read_excel(temp_file)
            
        # Convert to object to allow empty strings, then fillna
        new_df = new_df.astype(object).fillna("")
        
        # Super fast vectorized cleaning
        for col in new_df.columns:
            new_df[col] = new_df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(' 00:00:00', '', regex=False)
            
        # Add search_col if it doesn't exist
        if '_search_col' not in new_df.columns:
            new_df['_search_col'] = new_df[new_df.columns[0]].str.cat(new_df[new_df.columns[1:]], sep=' ').str.lower()
            
        # Append to existing
        # Ignore index to add them at the bottom
        df = pd.concat([df, new_df], ignore_index=True)
        
        # Fill any NaNs created by missing columns in new_df
        df = df.astype(object).fillna("")
        # Make sure they're strings
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
                
        # Save to disk
        save_data()
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        return {"status": "success", "message": f"{len(new_df)} members uploaded successfully!"}
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/template")
def download_template():
    # Exclude internal columns
    export_cols = [c for c in df.columns if c != '_search_col']
    template_df = pd.DataFrame(columns=export_cols)
    temp_file = "template.xlsx"
    template_df.to_excel(temp_file, index=False, engine='openpyxl')
    return FileResponse(temp_file, filename="Member_Template.xlsx")



@app.get("/download")
def download_excel(query: str = Query("")):
    if df.empty:
        return {"error": "Data file not found or empty"}

    filtered_df = df
    if query:
        mask = filtered_df['_search_col'].str.contains(query.lower(), na=False)
        filtered_df = filtered_df[mask]
    
    export_df = filtered_df.drop(columns=['_search_col'])
    
    temp_file = "filtered_results.xlsx"
    export_df.to_excel(temp_file, index=False)
    
    return FileResponse(
        temp_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="members_search_results.xlsx"
    )
