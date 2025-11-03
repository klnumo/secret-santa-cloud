from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from .supabase import supabase, supabase_admin
import uuid
import random
from jose import jwt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="backend/frontend"), name="static")

def get_current_user(authorization: str = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.get_unverified_claims(token)
        return {"sub": payload["sub"], "email": payload.get("email")}
    except:
        raise HTTPException(401, "Invalid token")

@app.get("/")
async def home():
    with open("../frontend/index.html") as f:
        return HTMLResponse(f.read())

@app.post("/create-group")
def create_group(name: str = Form(...), user=Depends(get_current_user)):
    res = supabase.table("groups").insert({
        "name": name,
        "creator_id": user["sub"]
    }).execute()
    return {"group_id": res.data[0]["id"]}

@app.post("/add-participant")
def add_participant(group_id: str = Form(...), name: str = Form(...), email: str = Form(...), user=Depends(get_current_user)):
    # Проверка: юзер — создатель группы
    group = supabase.table("groups").select("creator_id").eq("id", group_id).execute()
    if not group.data or group.data[0]["creator_id"] != user["sub"]:
        raise HTTPException(403, "Not owner")
    
    supabase.table("participants").insert({
        "group_id": group_id,
        "name": name,
        "email": email
    }).execute()
    return {"status": "added"}

@app.post("/launch/{group_id}")
def launch_santa(group_id: str, user=Depends(get_current_user)):
    group = supabase.table("groups").select("creator_id").eq("id", group_id).execute()
    if not group.data or group.data[0]["creator_id"] != user["sub"]:
        raise HTTPException(403, "Not owner")
    
    parts = supabase.table("participants").select("id").eq("group_id", group_id).execute().data
    if len(parts) < 3:
        raise HTTPException(400, "Need at least 3 participants")
    
    ids = [p["id"] for p in parts]
    targets = ids[1:] + [ids[0]]
    random.shuffle(targets)
    
    for p, t in zip(parts, targets):
        supabase_admin.table("participants").update({"target_id": t}).eq("id", p["id"]).execute()
    
    return {"status": "launched"}

@app.get("/group/{group_id}")
def get_group(group_id: str):
    group = supabase.table("groups").select("name").eq("id", group_id).execute()
    parts = supabase.table("participants").select("name, email, target_id").eq("group_id", group_id).execute().data
    return {"group": group.data[0] if group.data else {}, "participants": parts}
