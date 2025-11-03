from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .supabase import supabase, supabase_admin
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="backend/frontend"), name="static")

# Простая проверка email
def validate_email(email: str):
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Некорректный email")
    return email.lower()

@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")

@app.post("/login")
async def login(email: str = Form(...)):
    email = validate_email(email)
    # Просто "логин" — сохраняем в сессии (через cookie)
    return {"user_id": email, "email": email}

@app.post("/create-group")
async def create_group(request: Request, name: str = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Не авторизован")
    res = supabase.table("groups").insert({"name": name, "creator_id": user_id}).execute()
    return {"group_id": res.data[0]["id"]}

@app.post("/add-participant")
async def add_participant(request: Request, group_id: str = Form(...), name: str = Form(...), email: str = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Не авторизован")
    owner = supabase.table("groups").select("creator_id").eq("id", group_id).execute()
    if not owner.data or owner.data[0]["creator_id"] != user_id:
        raise HTTPException(403, "Ты не владелец")
    validate_email(email)
    supabase.table("participants").insert({"group_id": group_id, "name": name, "email": email}).execute()
    return {"status": "ok"}

@app.post("/launch/{group_id}")
async def launch(group_id: str, request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Не авторизован")
    owner = supabase.table("groups").select("creator_id").eq("id", group_id).execute()
    if not owner.data or owner.data[0]["creator_id"] != user_id:
        raise HTTPException(403, "Ты не владелец")
    parts = supabase.table("participants").select("id").eq("group_id", group_id).execute().data
    if len(parts) < 3:
        raise HTTPException(400, "Нужно 3+ участников")
    ids = [p["id"] for p in parts]
    targets = ids[1:] + [ids[0]]
    random.shuffle(targets)
    for p, t in zip(ids, targets):
        supabase_admin.table("participants").update({"target_id": t}).eq("id", p).execute()
    return {"status": "launched"}

@app.get("/group/{group_id}")
async def get_group(group_id: str):
    group = supabase.table("groups").select("name").eq("id", group_id).execute()
    parts = supabase.table("participants").select("name,email,target_id").eq("group_id", group_id).execute().data
    return {
        "name": group.data[0]["name"] if group.data else "",
        "participants": parts
    }
