import hashlib
from database import read_ballots, save_ballots


# =========================
# HASH HESAPLAMA
# =========================
def calculate_hash(token: str, encrypted_vote: str, timestamp: str, previous_hash: str) -> str:
    raw_data = f"{token}{encrypted_vote}{timestamp}{previous_hash}"
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()


def get_last_hash() -> str:
    ballots = read_ballots()

    if not ballots:
        return "0" * 64

    last_ballot = ballots[-1]
    return last_ballot.get("current_hash", "0" * 64)


# =========================
# ZİNCİR DOĞRULAMA
# =========================
def verify_chain() -> bool:
    ballots = read_ballots()

    if not ballots:
        return True

    expected_previous_hash = "0" * 64

    for ballot in ballots:
        token = ballot.get("token", "")
        encrypted_vote = ballot.get("encrypted_vote", "")
        timestamp = ballot.get("timestamp", "")
        previous_hash = ballot.get("previous_hash", "")
        current_hash = ballot.get("current_hash", "")

        if previous_hash != expected_previous_hash:
            return False

        recalculated_hash = calculate_hash(token, encrypted_vote, timestamp, previous_hash)
        if recalculated_hash != current_hash:
            return False

        expected_previous_hash = current_hash

    return True


# =========================
# ZİNCİRİ YENİDEN OLUŞTURMA
# =========================
def rebuild_chain() -> tuple[bool, str]:
    ballots = read_ballots()

    if not ballots:
        return True, "Sandık boş. Yeniden oluşturulacak kayıt yok."

    previous_hash = "0" * 64

    try:
        for ballot in ballots:
            token = ballot.get("token", "")
            encrypted_vote = ballot.get("encrypted_vote", "")
            timestamp = ballot.get("timestamp", "")

            ballot["previous_hash"] = previous_hash
            ballot["current_hash"] = calculate_hash(
                token,
                encrypted_vote,
                timestamp,
                previous_hash
            )

            previous_hash = ballot["current_hash"]

        save_ballots(ballots)
        return True, "Hash zinciri başarıyla yeniden oluşturuldu."
    except Exception as e:
        return False, f"Hash zinciri yeniden oluşturulamadı: {e}"


# =========================
# TEST
# =========================
if __name__ == "__main__":
    success, message = rebuild_chain()
    print(message)

    if verify_chain():
        print("Hash zinciri sağlam.")
    else:
        print("Hash zinciri bozulmuş.")
