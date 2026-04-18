from database import read_ballots
from crypto_utils import decrypt_vote
from integrity import verify_chain


def count_votes():
    if not verify_chain():
        print("❌ Sandık açılamaz. Veri bütünlüğü bozulmuş.")
        return

    ballots = read_ballots()

    if not ballots:
        print("Sandık boş.")
        return

    results = {}

    print("\n=== ÇÖZÜLEN OYLAR ===")
    for i, ballot in enumerate(ballots, start=1):
        try:
            vote = decrypt_vote(ballot["encrypted_vote"])
            print(f"{i}. oy: {vote}")
            results[vote] = results.get(vote, 0) + 1
        except Exception as e:
            print(f"❌ {i}. oy çözülemedi: {e}")
            return

    print("\n=== SEÇİM SONUÇLARI ===")
    for party, count in results.items():
        print(f"{party}: {count} oy")


if __name__ == "__main__":
    count_votes()
