from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import datetime
import uuid
from fastapi.templating import Jinja2Templates

# Import from sibling/parent modules
from agent.rag import init_agent, retrieve_context, generate_response
from database import init_db, get_chats_collection, get_user_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing models and vector database...")
    init_db()
    init_agent()
    yield
    print("Cleaning up resources...")

app = FastAPI(lifespan=lifespan)

# Assuming static folder is in Backend/static
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def delete_empty_sessions():
    try:
        chats_col = get_chats_collection()
        if chats_col is not None:
            result = chats_col.delete_many({"messages": []})
            return result.deleted_count
        return 0
    except Exception as e:
        print(f"Failed to delete empty sessions: {str(e)}")
        return 0

@app.post("/start_session")
async def start_session(request: Request):
    data = await request.json()
    UID = data.get("UID")

    deleted_count = delete_empty_sessions()
    print(f"Deleted {deleted_count} empty sessions before starting a new session")

    session_id = str(uuid.uuid4())
    chats_col = get_chats_collection()
    chats_col.insert_one({
        "UID": UID,
        "session_id": session_id,
        "messages": [],
        "created_at": datetime.datetime.now()
    })
    return {"session_id": session_id}

@app.post("/registration")
async def register_user(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email, and password are required")

    UID = str(uuid.uuid4())

    user = {
        "UID": UID,
        "name": name,
        "email": email,
        "password": password,
        "created_at": datetime.datetime.now()
    }
    user_col = get_user_collection()
    user_col.insert_one(user)
    return {"message": "User registered successfully"}

@app.post("/login")
async def login_user(request: Request):
    data = await request.json()
    username = data.get("name")
    password = data.get("password")
    print(username)

    if not username or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user_col = get_user_collection()
    user = user_col.find_one({"name": username, "password": password})
    if user:
        return {"message": "Login successful", "UID": user["UID"]}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/query")
async def receive_query(request: Request):
    data = await request.json()
    query = data.get("query")
    session_id = data.get("session_id")
    print(session_id)

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    print(f"Received query: {query}")
    context = retrieve_context(query)
    answer = generate_response(query, context)
    print(answer)

    chat = {
        "user": query,
        "context": context,
        "chatbot": answer,
        "timestamp": datetime.datetime.now()
    }

    chats_col = get_chats_collection()
    chats_col.update_one(
        {"session_id": session_id},
        {"$push": {"messages": chat}}
    )

    return {"response": answer}

@app.post("/chats")
async def get_chats_post(request: Request):
    try:
        data = await request.json()
        UID = data.get("UID")
        chats_col = get_chats_collection()
        chats = list(chats_col.find({"UID": UID}))
        for chat in chats:
            chat["_id"] = str(chat["_id"])
        return chats[::-1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chats: {str(e)}")

@app.get("/query")
async def get_query():
    return {"response": "Hello"}

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/hello")
async def get_name():
    return {"message": "Hello"}

@app.get("/chats/{session_id}")
async def get_chats_get(session_id: str):
    chats_col = get_chats_collection()
    session = chats_col.find_one({"session_id": session_id})
    if session:
        session["_id"] = str(session["_id"])
        return session
    else:
        raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
