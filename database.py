import os
from typing import Any

from secure_storage import load_secure_json, save_secure_json

DATA_DIR = "data"
VOTERS_FILE = os.path.join(DATA_DIR, "secmenler.json")
BALLOT_FILE = os.path.join(DATA_DIR, "sandik.json")


# =========================
# TEMEL DOSYA İŞLEMLERİ
# =========================
def ensure_data_folder() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def create_json_files() -> None:
    ensure_data_folder()

    if not os.path.exists(VOTERS_FILE):
        save_secure_json(VOTERS_FILE, [])

    if not os.path.exists(BALLOT_FILE):
        save_secure_json(BALLOT_FILE, [])


# =========================
# TC YARDIMCI FONKSİYONLARI
# =========================
def is_valid_tc(tc: str) -> bool:
    tc = tc.strip()
    return tc.isdigit() and len(tc) == 11


def mask_tc(tc: str) -> str:
    tc = tc.strip()

    if len(tc) != 11:
        return "***********"

    return f"{tc[:3]}*****{tc[-3:]}"


# =========================
# SEÇMEN VERİSİ
# =========================
def read_voters() -> list[dict]:
    create_json_files()

    voters = load_secure_json(VOTERS_FILE, [])

    if isinstance(voters, list):
        return voters

    return []


def save_voters(voters: list[dict]) -> None:
    save_secure_json(VOTERS_FILE, voters)


def import_voters_from_txt(file_path: str) -> tuple[bool, str]:
    """
    TXT dosyasından seçmen listesi içe aktarır.
    Her satırda 1 TC olacak şekilde beklenir.
    Geçersiz ve tekrar eden kayıtlar ayıklanır.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        unique_voters = []
        seen_tcs = set()

        for line in lines:
            tc = line.strip()

            if not tc:
                continue

            if not is_valid_tc(tc):
                continue

            if tc in seen_tcs:
                continue

            seen_tcs.add(tc)

            unique_voters.append({
                "tc": tc,
                "oy_kullandi": False,
                "token_hash": None
            })

        if not unique_voters:
            return False, "Geçerli TC bulunamadı."

        save_voters(unique_voters)

        return True, f"{len(unique_voters)} seçmen başarıyla sisteme aktarıldı."

    except Exception as e:
        return False, f"TC listesi aktarılırken hata oluştu: {e}"


def get_voter_stats() -> dict:
    voters = read_voters()

    total = len(voters)
    voted = sum(1 for voter in voters if voter.get("oy_kullandi"))
    not_voted = total - voted

    voted_percentage = (voted / total * 100) if total > 0 else 0
    not_voted_percentage = (not_voted / total * 100) if total > 0 else 0

    return {
        "toplam_secmen": total,
        "oy_kullanan": voted,
        "oy_kullanmayan": not_voted,
        "oy_kullanan_yuzde": round(voted_percentage, 2),
        "oy_kullanmayan_yuzde": round(not_voted_percentage, 2)
    }


# =========================
# SANDIK VERİSİ
# =========================
def read_ballots() -> list[dict]:
    create_json_files()

    ballots = load_secure_json(BALLOT_FILE, [])

    if isinstance(ballots, list):
        return ballots

    return []


def save_ballots(ballots: list[dict]) -> None:
    save_secure_json(BALLOT_FILE, ballots)


# =========================
# TEST / BAKIM İŞLEMLERİ
# =========================
def reset_voters_vote_status() -> None:
    voters = read_voters()

    for voter in voters:
        voter["oy_kullandi"] = False
        voter["token_hash"] = None

    save_voters(voters)


def reset_ballots() -> None:
    save_ballots([])


def reset_all_election_data() -> None:
    reset_voters_vote_status()
    reset_ballots()


# =========================
# DEBUG / KONTROL
# =========================
def show_data() -> None:
    voters = read_voters()
    ballots = read_ballots()

    print("=== Seçmenler ===")
    for voter in voters:
        print(voter)

    print("\n=== Sandık ===")
    for ballot in ballots:
        print(ballot)

    print("\n=== İstatistik ===")
    print(get_voter_stats())


if __name__ == "__main__":
    create_json_files()
    show_data()
