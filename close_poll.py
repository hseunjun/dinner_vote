import os
import json
import requests
from datetime import datetime, timezone, timedelta

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

def today_str():
    return datetime.now(KST).strftime("%Y-%m-%d")

def is_weekday_kst():
    return datetime.now(KST).weekday() < 5

def stop_telegram_poll(token, chat_id, message_id):
    url = f"https://api.telegram.org/bot{token}/stopPoll"
    data = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    response = requests.post(url, data=data)
    return response.json()

def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=data)
    return response.json()

def main():
    if not is_weekday_kst():
        print("주말이므로 종료하지 않습니다.")
        return

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    poll_state = load_json(STATE_FILE, {
        "chat_id": "",
        "message_id": "",
        "poll_id": "",
        "date": "",
        "status": "idle"
    })

    if poll_state.get("date") != today_str():
        print("오늘 날짜의 투표가 없습니다.")
        return

    if poll_state.get("status") != "open":
        print("열려 있는 투표가 없습니다.")
        return

    # Poll 종료
    stop_result = stop_telegram_poll(token, poll_state["chat_id"], poll_state["message_id"])

    if not stop_result.get("ok"):
        print(f"투표 종료 실패: {stop_result}")
        return

    poll = stop_result["result"]

    # 응답 파일에서 이름 목록 읽기
    answers_data = load_json(ANSWERS_FILE, {
        "poll_id": "",
        "date": "",
        "answers": {}
    })

    yes_names = []
    no_names = []

    for _, item in answers_data.get("answers", {}).items():
        name = item.get("name", "이름없음")
        answer = item.get("answer", "미응답")

        if answer == "네":
            yes_names.append(name)
        elif answer == "아니요":
            no_names.append(name)

    yes_names.sort()
    no_names.sort()

    yes_text = "\n".join([f"• {name}" for name in yes_names]) if yes_names else "없음"
    no_text = "\n".join([f"• {name}" for name in no_names]) if no_names else "없음"

    result_text = f"""📊 오늘 저녁 식사 설문 결과

<b>식사 예정 ({len(yes_names)}명)</b>
{yes_text}

<b>불참 ({len(no_names)}명)</b>
{no_text}

총 응답 인원: {len(yes_names) + len(no_names)}명"""

    send_result = send_telegram_message(token, poll_state["chat_id"], result_text)

    if send_result.get("ok"):
        poll_state["status"] = "closed"
        save_json(STATE_FILE, poll_state)
        print("투표 종료 및 결과 전송 완료")
    else:
        print(f"결과 메시지 전송 실패: {send_result}")

if __name__ == "__main__":
    main()
