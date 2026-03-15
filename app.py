import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import json
import uuid

app = Flask(__name__)

# -------------------------
# Load API Key from .env
# -------------------------
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

# -------------------------
# Groq Client
# -------------------------
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

# -------------------------
# Chat History File
# -------------------------
HISTORY_FILE = "chat_history.json"


def load_chats():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_chats(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -------------------------
# Home Page
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# Create New Chat
# -------------------------
@app.route("/new_chat", methods=["POST"])
def new_chat():

    chats = load_chats()

    chat_id = str(uuid.uuid4())

    chats[chat_id] = {
        "title": "New Chat",
        "messages": []
    }

    save_chats(chats)

    return jsonify({"chat_id": chat_id})


# -------------------------
# Get All Chats
# -------------------------
@app.route("/get_chats")
def get_chats():

    chats = load_chats()

    return jsonify(chats)


# -------------------------
# Chat API
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    user_message = data.get("message")
    chat_id = data.get("chat_id")

    if not user_message or not chat_id:
        return jsonify({"error": "Message or chat_id missing"}), 400

    chats = load_chats()

    if chat_id not in chats:
        chats[chat_id] = {
            "title": "New Chat",
            "messages": []
        }

    # -------------------------
    # GroqAI API Call
    # -------------------------
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # -------------------------
    # Extract Bot Reply
    # -------------------------
    bot_reply = "No response"

    try:
        bot_reply = completion.choices[0].message.content
    except Exception as e:
        print("Error:", e)

    # -------------------------
    # Set Title from First Message
    # -------------------------
    if chats[chat_id]["title"] == "New Chat":
        chats[chat_id]["title"] = user_message[:30]

    # -------------------------
    # Save Messages
    # -------------------------
    chats[chat_id]["messages"].append({
        "user": user_message,
        "bot": bot_reply
    })

    save_chats(chats)

    return jsonify({"reply": bot_reply})


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)