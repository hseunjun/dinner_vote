import os
import json
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import Application, PollAnswerHandler, ContextTypes

STATE_FILE = "state/poll_state.json"
ANSWERS_FILE = "state/poll_answers.json"
KST = timezone(timedelta(hours=9))

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_display_name(user):
    if user.full_name:
        return user.full_name
    if user.username:
        return f"@{user.username}"
    return str(user.id)

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if not answer:
        return

    poll_state = load_json(STATE_FILE, {
        "chat_id": "",
        "message_id": "",
        "poll_id": "",
        "date": "",
        "status": "idle"
    })

    if poll_state.get("status") != "open":
        return

    if answer.poll_id != poll_state.get("poll_id"):
        return

    answers_data = load_json(ANSWERS_FILE, {
        "poll_id": poll_state.get("poll_id", ""),
        "date": poll_state.get("date", ""),
        "answers": {}
    })

    if answers_data.get("poll_id") != poll_state.get("poll_id"):
        answers_data = {
            "poll_id": poll_state.get("poll_id", ""),
            "date": poll_state.get("date", ""),
            "answers": {}
        }

    selected = "미응답"
    if answer.option_ids == [0]:
        selected = "네"
    elif answer.option_ids == [1]:
        selected = "아니요"
    elif answer.option_ids == []:
        selected = "미응답"

    user_id = str(answer.user.id)
    answers_data["answers"][user_id] = {
        "name": get_display_name(answer.user),
        "username": answer.user.username or "",
        "answer": selected,
        "updated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }

    save_json(ANSWERS_FILE, answers_data)

async def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    app = Application.builder().token(token).build()
    app.add_handler(PollAnswerHandler(receive_poll_answer))

    print("bot_listener 시작")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
