import json
import os
import hashlib
import tempfile
from datetime import datetime

LOG_FILE = "data/audit_log.json"


def ensure_log_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)


def _atomic_write_json(path: str, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        delete=False
    ) as tmp_file:
        json.dump(data, tmp_file, ensure_ascii=False, indent=4)
        temp_name = tmp_file.name

    os.replace(temp_name, path)


def read_logs() -> list[dict]:
    ensure_log_file()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            return logs if isinstance(logs, list) else []
    except Exception:
        return []


def calculate_log_hash(timestamp: str, event_type: str, detail: str, previous_hash: str) -> str:
    raw_data = f"{timestamp}{event_type}{detail}{previous_hash}"
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()


def get_last_log_hash() -> str:
    logs = read_logs()
    if not logs:
        return "0" * 64
    return logs[-1].get("current_hash", "0" * 64)


def add_log(event_type: str, detail: str) -> None:
    logs = read_logs()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    previous_hash = get_last_log_hash()
    current_hash = calculate_log_hash(timestamp, event_type, detail, previous_hash)

    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "detail": detail,
        "previous_hash": previous_hash,
        "current_hash": current_hash
    }

    logs.append(log_entry)
    _atomic_write_json(LOG_FILE, logs)


def verify_log_chain() -> bool:
    logs = read_logs()

    if not logs:
        return True

    expected_previous_hash = "0" * 64

    for log in logs:
        timestamp = log.get("timestamp", "")
        event_type = log.get("event_type", "")
        detail = log.get("detail", "")
        previous_hash = log.get("previous_hash", "")
        current_hash = log.get("current_hash", "")

        if previous_hash != expected_previous_hash:
            return False

        recalculated_hash = calculate_log_hash(timestamp, event_type, detail, previous_hash)
        if recalculated_hash != current_hash:
            return False

        expected_previous_hash = current_hash

    return True


def format_logs_for_display() -> str:
    logs = read_logs()

    if not logs:
        return "Henüz log kaydı yok."

    lines = []
    for i, log in enumerate(logs, start=1):
        lines.append(f"[{i}] {log['timestamp']} | {log['event_type']}")
        lines.append(f"    Detay: {log['detail']}")
        lines.append(f"    Prev : {log['previous_hash'][:16]}...")
        lines.append(f"    Hash : {log['current_hash'][:16]}...")
        lines.append("")

    lines.append(
        "LOG ZİNCİRİ DURUMU: SAĞLAM"
        if verify_log_chain()
        else "LOG ZİNCİRİ DURUMU: BOZULMUŞ"
    )

    return "\n".join(lines)


if __name__ == "__main__":
    add_log("TEST", "Audit log sistemi test edildi.")
    print(format_logs_for_display())
