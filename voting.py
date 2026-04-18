import json
from database import VOTERS_FILE, BALLOT_FILE, read_voters, read_ballots
from crypto_utils import encrypt_vote, generate_keys
import secrets


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

            voter["token"] = token
            voter["oy_kullandi"] = True

            ballot = {
                "token": token,
                "encrypted_vote": encrypted_vote
            }

            ballots.append(ballot)

            save_voters(voters)
            save_ballots(ballots)

            print("✅ Oy başarıyla kaydedildi!")
            print("Token:", token)
            return

    print("❌ Seçmen bulunamadı!")


if __name__ == "__main__":
    tc = input("TC Kimlik No: ")
    vote_choice = input("Oy tercihi: ")
    vote(tc, vote_choice)
