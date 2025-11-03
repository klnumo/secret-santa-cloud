from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .supabase import supabase, supabase_admin
import random
import os

app = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# === АВТОРИЗАЦИЯ ПО EMAIL ===
def validate_email(email: str):
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Некоррект, нужен @ и .")
    return email.lower()

def get_user(request: Request):
    user = request.cookies.get("user_id")
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return user

# === СТРАНИЦЫ ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse("/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(email: str = Form(...)):
    user_id = validate_email(email)
    response = RedirectResponse("/create", status_code=302)
    response.set_cookie(key="user_id", value=user_id, httponly=True)
    return response

@app.get("/create", response_class=HTMLResponse)
async def create_group_page(request: Request, user: str = Depends(get_user)):
    return templates.TemplateResponse("create_group.html", {"request": request})

@app.post("/create")
async def create_group(request: Request, name: str = Form(...), user: str = Depends(get_user)):
    res = supabase.table("groups").insert({"name": name, "creator_id": user}).execute()
    group_id = res.data[0]["id"]
    return RedirectResponse(f"/group/{group_id}", status_code=302)

@app.get("/group/{group_id}", response_class=HTMLResponse)
async def group_page(request: Request, group_id: str):
    user = request.cookies.get("user_id")
    group = supabase.table("groups").select("name, creator_id").eq("id", group_id).execute()
    if not group.data:
        raise HTTPException(404, "Группа не найдена")
    parts = supabase.table("participants").select("name,email,target_id").eq("group_id", group_id).execute().data
    return templates.TemplateResponse("group.html", {
        "request": request,
        "group": group.data[0],
        "participants": parts,
        "is_owner": user == group.data[0]["creator_id"],
        "group_id": group_id
    })

@app.post("/add-participant")
async def add_participant(group_id: str = Form(...), name: str = Form(...), email: str = Form(...), user: str = Depends(get_user)):
    validate_email(email)
    supabase.table("participants").insert({"group_id": group_id, "name": name, "email": email}).execute()
    return RedirectResponse(f"/group/{group_id}", status_code=302)

@app.post("/launch/{group_id}")
async def launch(group_id: str, user: str = Depends(get_user)):
    owner = supabase.table("groups").select("creator_id").eq("id", group_id).execute()
    if not owner.data or owner.data[0]["creator_id"] != user:
        raise HTTPException(403, "Ты не владелец")
    parts = supabase.table("participants").select("id").eq("group_id", group_id).execute().data
    if len(parts) < 3:
        raise HTTPException(400, "Нужно 3+ участников")
    ids = [p["id"] for p in parts]
    targets = ids[1:] + [ids[0]]
    random.shuffle(targets)
    for p, t in zip(ids, targets):
        supabase_admin.table("participants").update({"target_id": t}).eq("id", p).execute()
    return RedirectResponse(f"/result/{group_id}", status_code=302)

@app.get("/result/{group_id}", response_class=HTMLResponse)
async def result_page(request: Request, group_id: str):
    group = supabase.table("groups").select("name").eq("id", group_id).execute()
    parts = supabase.table("participants").select("name,email,target_id").eq("group_id", group_id).execute().data
    return templates.TemplateResponse("result.html", {
        "request": request,
        "group_name": group.data[0]["name"] if group.data else "",
        "participants": parts
    })