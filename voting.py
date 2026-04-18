import json
import secrets
from database import VOTERS_FILE, BALLOT_FILE, read_voters, read_ballots
from crypto_utils import encrypt_vote, generate_keys, encrypt_file
from integrity import calculate_hash, get_last_hash


def save_voters(voters):
    with open(VOTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(voters, f, ensure_ascii=False, indent=4)


def save_ballots(ballots):
    with open(BALLOT_FILE, "w", encoding="utf-8") as f:
        json.dump(ballots, f, ensure_ascii=False, indent=4)


def generate_token():
    return secrets.token_hex(8)


def vote(tc, vote_choice):
    generate_keys()

    voters = read_voters()
    ballots = read_ballots()

    for voter in voters:
        if voter["tc"] == tc:
            if voter["oy_kullandi"]:
                print("❌ Bu kişi zaten oy kullanmış!")
                return

            token = generate_token()
            encrypted_vote = encrypt_vote(vote_choice)
            previous_hash = get_last_hash()
            current_hash = calculate_hash(token, encrypted_vote, previous_hash)

            voter["token"] = token
            voter["oy_kullandi"] = True

            ballot = {
                "token": token,
                "encrypted_vote": encrypted_vote,
                "previous_hash": previous_hash,
                "current_hash": current_hash
            }

            ballots.append(ballot)

            save_voters(voters)
            save_ballots(ballots)

            encrypt_file("data/sandik.json", "data/sandik.enc")

            print("✅ Oy başarıyla kaydedildi!")
            print("Token:", token)
            print("🔐 Sandık dosyasının AES şifreli kopyası oluşturuldu.")
            return

    print("❌ Seçmen bulunamadı!")


if __name__ == "__main__":
    tc = input("TC Kimlik No: ")
    vote_choice = input("Oy tercihi: ")
    vote(tc, vote_choice)
