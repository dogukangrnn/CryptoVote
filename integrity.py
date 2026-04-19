import hashlib
from database import read_ballots


def calculate_hash(token, encrypted_vote, timestamp, previous_hash):
    data = f"{token}{encrypted_vote}{timestamp}{previous_hash}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def get_last_hash():
    ballots = read_ballots()
    if not ballots:
        return "0"
    return ballots[-1]["current_hash"]


def verify_chain():
    ballots = read_ballots()

    if not ballots:
        print("Sandık boş, doğrulanacak kayıt yok.")
        return True

    previous_hash = "0"

    for i, ballot in enumerate(ballots):
        expected_hash = calculate_hash(
            ballot["token"],
            ballot["encrypted_vote"],
            ballot["timestamp"],
            ballot["previous_hash"]
        )

        if ballot["previous_hash"] != previous_hash:
            print(f"❌ Zincir koptu! Kayıt sırası bozuk. Kayıt no: {i + 1}")
            return False

        if ballot["current_hash"] != expected_hash:
            print(f"❌ Veri bütünlüğü bozulmuş! Kayıt no: {i + 1}")
            return False

        previous_hash = ballot["current_hash"]

    print("✅ Hash zinciri sağlam.")
    return True


if __name__ == "__main__":
    verify_chain()
