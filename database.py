import json
import os
import tempfile
from typing import Any

from crypto_utils import encrypt_file, decrypt_file_to_bytes

DATA_DIR = "data"
VOTERS_FILE = os.path.join(DATA_DIR, "secmenler.json")
BALLOT_FILE = os.path.join(DATA_DIR, "sandik.json")
BALLOT_ENC_FILE = os.path.join(DATA_DIR, "sandik.enc")


# =========================
# TEMEL DOSYA İŞLEMLERİ
# =========================
def ensure_data_folder() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _atomic_write_text(path: str, text: str) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        delete=False
    ) as tmp_file:
        tmp_file.write(text)
        temp_name = tmp_file.name

    os.replace(temp_name, path)


def _safe_json_load(path: str, default: Any):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: str, data: Any) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=4)
    _atomic_write_text(path, text)


def _sync_ballot_encrypted_copy() -> None:
    """
    sandik.json güncellendiğinde şifreli kopyasını da üretir.
    """
    if os.path.exists(BALLOT_FILE):
        encrypt_file(BALLOT_FILE, BALLOT_ENC_FILE)


# =========================
# BAŞLATMA
# =========================
def create_json_files() -> None:
    ensure_data_folder()

    if not os.path.exists(VOTERS_FILE):
        _write_json(VOTERS_FILE, [])

    if not os.path.exists(BALLOT_FILE):
        _write_json(BALLOT_FILE, [])

    if not os.path.exists(BALLOT_ENC_FILE):
        _sync_ballot_encrypted_copy()


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
    voters = _safe_json_load(VOTERS_FILE, [])
    return voters if isinstance(voters, list) else []


def save_voters(voters: list[dict]) -> None:
    _write_json(VOTERS_FILE, voters)


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

    # Öncelik düz json dosyası
    ballots = _safe_json_load(BALLOT_FILE, None)
    if isinstance(ballots, list):
        return ballots

    # Eğer json bozuksa şifreli kopyadan çözmeyi dene
    if os.path.exists(BALLOT_ENC_FILE):
        try:
            raw = decrypt_file_to_bytes(BALLOT_ENC_FILE)
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    return []


def save_ballots(ballots: list[dict]) -> None:
    _write_json(BALLOT_FILE, ballots)
    _sync_ballot_encrypted_copy()


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
