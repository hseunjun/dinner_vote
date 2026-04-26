import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

KST = timezone(timedelta(hours=9))
STATE_FILE = "state/poll_state.json"
ANSWERS_FILE = "state/poll_answers.json"

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]        # 예: yourname/telegram-dinner-bot
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

def now_kst_iso():
    return datetime.now(KST).isoformat()

def github_get_file(path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    params = {"ref": GITHUB_BRANCH}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content), data["sha"]

def github_put_file(path, obj, message):
    old_obj, sha = github_get_file(path)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    content = base64.b64encode(
        json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": message,
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

@app.get("/")
def health():
    return jsonify({"ok": True, "message": "telegram poll webhook is running"})

@app.post(f"/telegram/webhook/{WEBHOOK_SECRET}")
def telegram_webhook():
    update = request.get_json(silent=True) or {}

    if "poll_answer" not in update:
        return jsonify({"ok": True, "ignored": True})

    poll_answer = update["poll_answer"]
    poll_id = poll_answer["poll_id"]
    user = poll_answer["user"]
    option_ids = poll_answer.get("option_ids", [])

    poll_answers, _ = github_get_file(ANSWERS_FILE)
    if not poll_answers:
        poll_answers = {
            "poll_id": poll_id,
            "date": datetime.now(KST).strftime("%Y-%m-%d"),
            "answers": {}
        }

    if poll_answers.get("poll_id") != poll_id:
        return jsonify({
            "ok": True,
            "ignored": True,
            "reason": "poll_id mismatch"
        })

    poll_answers["answers"][str(user["id"])] = {
        "user_id": user["id"],
        "name": (
            f'{user.get("first_name", "")} {user.get("last_name", "")}'.strip()
            or user.get("username", "")
        ),
        "username": user.get("username"),
        "option_ids": option_ids,
        "updated_at": now_kst_iso()
    }

    github_put_file(
        ANSWERS_FILE,
        poll_answers,
        f"Update poll answer for user {user['id']}"
    )

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
