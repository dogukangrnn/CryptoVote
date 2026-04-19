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
    create_json_files()
    with open(VOTERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def read_ballots():
    create_json_files()
    with open(BALLOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_voters(voters):
    with open(VOTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(voters, f, ensure_ascii=False, indent=4)


def add_voter(tc):
    tc = tc.strip()

    if not tc.isdigit() or len(tc) != 11:
        return False, "TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır."

    voters = read_voters()

    for voter in voters:
        if voter["tc"] == tc:
            return False, "Bu seçmen zaten kayıtlı."

    voters.append({
        "tc": tc,
        "oy_kullandi": False,
        "token": None
    })

    save_voters(voters)
    return True, "Yeni seçmen başarıyla eklendi."


def delete_voter(tc):
    tc = tc.strip()
    voters = read_voters()

    for voter in voters:
        if voter["tc"] == tc:
            if voter["oy_kullandi"]:
                return False, "Oy kullanmış seçmen silinemez."

            voters.remove(voter)
            save_voters(voters)
            return True, "Seçmen başarıyla silindi."

    return False, "Silinecek seçmen bulunamadı."


def update_voter(old_tc, new_tc):
    old_tc = old_tc.strip()
    new_tc = new_tc.strip()

    if not new_tc.isdigit() or len(new_tc) != 11:
        return False, "Yeni TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır."

    voters = read_voters()

    for voter in voters:
        if voter["tc"] == new_tc:
            return False, "Yeni TC zaten başka bir seçmene ait."

    for voter in voters:
        if voter["tc"] == old_tc:
            if voter["oy_kullandi"]:
                return False, "Oy kullanmış seçmen düzenlenemez."

            voter["tc"] = new_tc
            save_voters(voters)
            return True, "Seçmen bilgisi başarıyla güncellendi."

    return False, "Güncellenecek seçmen bulunamadı."


def list_voters():
    return read_voters()


def get_voter_stats():
    voters = read_voters()
    total = len(voters)

    voted = sum(1 for voter in voters if voter["oy_kullandi"])
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
    print("JSON veri dosyaları hazır.")
    show_data()

    print("\n=== İstatistik ===")
    print(get_voter_stats())
