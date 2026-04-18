import json
import secrets
from database import VOTERS_FILE, BALLOT_FILE, read_voters, read_ballots

def save_voters(voters):
    with open(VOTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(voters, f, ensure_ascii=False, indent=4)

def save_ballots(ballots):
    with open(BALLOT_FILE, "w", encoding="utf-8") as f:
        json.dump(ballots, f, ensure_ascii=False, indent=4)

def generate_token():
    return secrets.token_hex(8)

def find_voter(tc):
    voters = read_voters()
    for voter in voters:
        if voter["tc"] == tc:
            return voter
    return None

def vote(tc, vote_choice):
    voters = read_voters()
    ballots = read_ballots()

    for voter in voters:
        if voter["tc"] == tc:

            if voter["oy_kullandi"]:
                print("❌ Bu kişi zaten oy kullanmış!")
                return

            # token üret
            token = generate_token()
            voter["token"] = token
            voter["oy_kullandi"] = True

            # oy kaydı (şimdilik şifreleme yok)
            ballot = {
                "token": token,
                "vote": vote_choice
            }

            ballots.append(ballot)

            save_voters(voters)
            save_ballots(ballots)

            print("✅ Oy başarıyla kaydedildi!")
            print("Token:", token)
            return

    print("❌ Seçmen bulunamadı!")

