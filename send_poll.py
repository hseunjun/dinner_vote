import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Bot

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

async def main():
    if not is_weekday_kst():
        print("주말이므로 발송하지 않습니다.")
        return

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    bot = Bot(token=token)

    message = await bot.send_poll(
        chat_id=chat_id,
        question="🍽 오늘 저녁 식사 하실 분?",
        options=["네", "아니요"],
        is_anonymous=False,
        allows_multiple_answers=False
    )

    poll_state = {
        "chat_id": str(chat_id),
        "message_id": message.message_id,
        "poll_id": message.poll.id,
        "date": today_str(),
        "status": "open"
    }

    poll_answers = {
        "poll_id": message.poll.id,
        "date": today_str(),
        "answers": {}
    }

    save_json(STATE_FILE, poll_state)
    save_json(ANSWERS_FILE, poll_answers)
    print("투표 발송 및 응답 파일 초기화 완료")

if __name__ == "__main__":
    asyncio.run(main())
