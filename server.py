import os
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import discord
from discord.ext import commands

app = FastAPI()

# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

TASKS = {}

class TaskData(BaseModel):
    name: str
    channel_id: int
    message: str
    delay: int

# --- Task Loop ---
async def repeater(name):
    while TASKS.get(name, {}).get("running"):
        task = TASKS[name]
        try:
            channel = bot.get_channel(task["channel_id"])
            if channel:
                await channel.send(task["message"])
        except Exception as e:
            print(f"Error sending message: {e}")

        await asyncio.sleep(task["delay"])

# --- API Routes ---
@app.post("/start")
async def start_task(data: TaskData):
    if data.name in TASKS:
        return {"error": "Task already exists"}

    TASKS[data.name] = {
        "channel_id": data.channel_id,
        "message": data.message,
        "delay": data.delay,
        "running": True
    }

    asyncio.create_task(repeater(data.name))
    return {"status": "started"}

@app.post("/stop/{name}")
async def stop_task(name: str):
    if name in TASKS:
        TASKS[name]["running"] = False
        return {"status": "stopped"}
    return {"error": "Task not found"}

@app.get("/tasks")
async def list_tasks():
    return TASKS

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")

# --- Start Bot with FastAPI ---
@app.on_event("startup")
async def startup_event():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set!")
        return
    asyncio.create_task(bot.start(token))
