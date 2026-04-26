import os
import json
import requests
from datetime import datetime, timezone, timedelta

STATE_FILE = "state/poll_state.json"
ANSWERS_FILE = "state/poll_answers.json"
KST = timezone(timedelta(hours=9))

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def stop_poll(token, chat_id, message_id):
    url = f"https://api.telegram.org/bot{token}/stopPoll"
    data = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    r = requests.post(url, data=data, timeout=30)
    return r.json()

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    r = requests.post(url, data=data, timeout=30)
    return r.json()

def display_name(answer):
    name = (answer.get("name") or "").strip()
    username = (answer.get("username") or "").strip()

    if name:
        return name
    if username:
        return f"@{username}"
    return "이름없음"

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    poll_state = load_json(STATE_FILE)
    poll_answers = load_json(ANSWERS_FILE)

    if poll_state.get("status") != "open":
        print("이미 종료된 투표입니다.")
        return

    chat_id = poll_state["chat_id"]
    message_id = poll_state["message_id"]

    stop_result = stop_poll(token, chat_id, message_id)
    if not stop_result.get("ok"):
        raise RuntimeError(f"stopPoll 실패: {stop_result}")

    attendees = []

    for _, answer in poll_answers.get("answers", {}).items():
        option_ids = answer.get("option_ids", [])
        if 0 in option_ids:
            attendees.append(display_name(answer))

    attendees = list(dict.fromkeys(attendees))

    if attendees:
        attendee_text = ", ".join(attendees)
        text = f"참석자: {attendee_text}\n17:30에 식당에서 만나요~^^"
    else:
        text = "참석자: 없음\n17:30에 식당에서 만나요~^^"

    msg_result = send_message(token, chat_id, text)
    if not msg_result.get("ok"):
        raise RuntimeError(f"sendMessage 실패: {msg_result}")

    poll_state["status"] = "closed"
    poll_state["closed_at"] = datetime.now(KST).isoformat()
    save_json(STATE_FILE, poll_state)

    print("투표 종료 및 결과 메시지 발송 완료")

if __name__ == "__main__":
    main()
