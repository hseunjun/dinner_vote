import os
import json
import requests
from datetime import datetime, timezone, timedelta

STATE_FILE = "state/poll_state.json"
ANSWERS_FILE = "state/poll_answers.json"
KST = timezone(timedelta(hours=9))

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_str():
    return datetime.now(KST).strftime("%Y-%m-%d")

def is_weekday_kst():
    return datetime.now(KST).weekday() < 5

def send_telegram_poll(token, chat_id, question, options):
    url = f"https://api.telegram.org/bot{token}/sendPoll"
    data = {
        "chat_id": chat_id,
        "question": question,
        "options": json.dumps(options),
        "is_anonymous": "false",
        "allows_multiple_answers": "false"
    }
    response = requests.post(url, data=data)
    return response.json()

def main():
    if not is_weekday_kst():
        print("주말이므로 발송하지 않습니다.")
        return

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    question = "🍽 오늘 저녁 식사 하실 분?"
    options = ["네", "아니요"]

    result = send_telegram_poll(token, chat_id, question, options)

    if result.get("ok"):
        message_id = result["result"]["message_id"]
        poll_id = result["result"]["poll"]["id"]

        poll_state = {
            "chat_id": str(chat_id),
            "message_id": message_id,
            "poll_id": poll_id,
            "date": today_str(),
            "status": "open"
        }

        poll_answers = {
            "poll_id": poll_id,
            "date": today_str(),
            "answers": {}
        }

        save_json(STATE_FILE, poll_state)
        save_json(ANSWERS_FILE, poll_answers)
        print(f"투표 발송 완료 - message_id: {message_id}")
    else:
        print(f"발송 실패: {result}")

if __name__ == "__main__":
    main()
