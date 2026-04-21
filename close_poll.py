import os
import json
from datetime import datetime, timezone, timedelta
from telegram import Bot

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

def build_name_lines(items):
    if not items:
        return "없음"
    return "\n".join([f"- {name}" for name in items])

def main():
    if not is_weekday_kst():
        print("주말이므로 종료하지 않습니다.")
        return

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    bot = Bot(token=token)

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

    poll = bot.stop_poll(
        chat_id=poll_state["chat_id"],
        message_id=poll_state["message_id"]
    )

    answers_data = load_json(ANSWERS_FILE, {
        "poll_id": "",
        "date": "",
        "answers": {}
    })

    yes_names = []
    no_names = []
    unknown_names = []

    for _, item in answers_data.get("answers", {}).items():
        name = item.get("name", "이름없음")
        answer = item.get("answer", "미응답")

        if answer == "네":
            yes_names.append(name)
        elif answer == "아니요":
            no_names.append(name)
        else:
            unknown_names.append(name)

    yes_names.sort()
    no_names.sort()
    unknown_names.sort()

    result_text = (
        "📊 오늘 저녁 식사 설문 결과\n\n"
        f"• 식사 예정 ({len(yes_names)}명)\n{build_name_lines(yes_names)}\n\n"
        f"• 불참 ({len(no_names)}명)\n{build_name_lines(no_names)}"
    )

    if unknown_names:
        result_text += f"\n\n• 응답 취소/기타 ({len(unknown_names)}명)\n{build_name_lines(unknown_names)}"

    total_voters = sum(option.voter_count for option in poll.options)
    result_text += f"\n\n총 응답 인원: {total_voters}명"

    bot.send_message(
        chat_id=poll_state["chat_id"],
        text=result_text
    )

    poll_state["status"] = "closed"
    save_json(STATE_FILE, poll_state)
    print("투표 종료 및 이름 포함 결과 전송 완료")

if __name__ == "__main__":
    main()
