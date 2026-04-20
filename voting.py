import json
import os
import secrets
import tempfile
import hashlib
from datetime import datetime

from database import VOTERS_FILE, BALLOT_FILE, read_voters, read_ballots
from crypto_utils import encrypt_vote, generate_keys, encrypt_file
from integrity import calculate_hash, get_last_hash, verify_chain


ALLOWED_PARTIES = {"A Partisi", "B Partisi", "C Partisi"}


# =========================
# DOSYA YAZMA YARDIMCILARI
# =========================
def atomic_write_json(path: str, data) -> None:
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


def save_voters(voters: list[dict]) -> None:
    atomic_write_json(VOTERS_FILE, voters)


def save_ballots(ballots: list[dict]) -> None:
    atomic_write_json(BALLOT_FILE, ballots)


# =========================
# DOĞRULAMA YARDIMCILARI
# =========================
def generate_token(existing_tokens: set[str]) -> str:
    while True:
        token = secrets.token_hex(16)
        if token not in existing_tokens:
            return token


def validate_tc(tc: str) -> tuple[bool, str]:
    tc = tc.strip()

    if not tc:
        return False, "TC Kimlik No boş bırakılamaz."

    if not tc.isdigit() or len(tc) != 11:
        return False, "TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır."

    return True, ""


def validate_vote_choice(vote_choice: str) -> tuple[bool, str]:
    vote_choice = vote_choice.strip()

    if vote_choice not in ALLOWED_PARTIES:
        return False, "Geçersiz oy tercihi."

    return True, ""


# =========================
# ANA OY VERME İŞLEMİ
# =========================
def vote(tc: str, vote_choice: str) -> tuple[bool, str]:
    tc = tc.strip()
    vote_choice = vote_choice.strip()

    is_valid_tc, tc_error = validate_tc(tc)
    if not is_valid_tc:
        return False, tc_error

    is_valid_vote, vote_error = validate_vote_choice(vote_choice)
    if not is_valid_vote:
        return False, vote_error

    # RSA anahtarlarını hazırla
    generate_keys()

    # Önce hash zinciri sağlam mı kontrol et
    if not verify_chain():
        return False, "Hash zinciri bozulmuş. Yeni oy eklenemez."

    voters = read_voters()
    ballots = read_ballots()

    voter = next((v for v in voters if v.get("tc") == tc), None)
    if voter is None:
        return False, "Seçmen bulunamadı."

    if voter.get("oy_kullandi"):
        return False, "Bu seçmen zaten oy kullanmış."

    existing_tokens = {b.get("token") for b in ballots if b.get("token")}
    token = generate_token(existing_tokens)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    encrypted_vote = encrypt_vote(vote_choice)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    previous_hash = get_last_hash()
    current_hash = calculate_hash(token, encrypted_vote, timestamp, previous_hash)

    ballot = {
        "token": token,
        "encrypted_vote": encrypted_vote,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
        "current_hash": current_hash
    }

    voter["oy_kullandi"] = True
    voter["token_hash"] = token_hash
    ballots.append(ballot)

    save_voters(voters)
    save_ballots(ballots)

    # Şifreli kopyayı da güncelle
    encrypt_file("data/sandik.json", "data/sandik.enc")

    return True, "Oy başarıyla kaydedildi."


# =========================
# TEST
# =========================
if __name__ == "__main__":
    tc = input("TC Kimlik No: ")
    vote_choice = input("Oy tercihi (A Partisi / B Partisi / C Partisi): ")

    success, message = vote(tc, vote_choice)
    print(message)
