import json
import os

VOTERS_FILE = "data/secmenler.json"
BALLOT_FILE = "data/sandik.json"


def ensure_data_folder():
    os.makedirs("data", exist_ok=True)


def create_json_files():
    ensure_data_folder()

    if not os.path.exists(VOTERS_FILE):
        sample_voters = [
            {"tc": "11111111111", "oy_kullandi": False, "token": None},
            {"tc": "22222222222", "oy_kullandi": False, "token": None},
            {"tc": "33333333333", "oy_kullandi": False, "token": None}
        ]
        with open(VOTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(sample_voters, f, ensure_ascii=False, indent=4)

    if not os.path.exists(BALLOT_FILE):
        with open(BALLOT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)


def read_voters():
    with open(VOTERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def read_ballots():
    with open(BALLOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def show_data():
    voters = read_voters()
    ballots = read_ballots()

    print("=== Seçmenler ===")
    for voter in voters:
        print(voter)

    print("\n=== Sandık ===")
    for ballot in ballots:
        print(ballot)


if __name__ == "__main__":
    create_json_files()
    print("JSON veri dosyaları hazırlandı.")
    show_data()
