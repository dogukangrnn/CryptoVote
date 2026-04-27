from database import read_ballots, save_ballots
from integrity import verify_chain


def main():
    print("=== MANİPÜLASYON TESTİ ===")

    ballots = read_ballots()

    if len(ballots) < 2:
        print("❌ Test için en az 2 oy kaydı gerekir.")
        return

    print("\n1) İlk zincir kontrolü:")
    if verify_chain():
        print("✅ Hash zinciri sağlam.")
    else:
        print("❌ Hash zinciri zaten bozuk.")
        return

    print("\n2) Sandıktaki 2. oyun encrypted_vote alanı değiştiriliyor...")

    original_vote = ballots[1]["encrypted_vote"]
    ballots[1]["encrypted_vote"] = "MANIPULE_EDILMIS_OY"

    save_ballots(ballots)

    print("\n3) Manipülasyon sonrası zincir kontrolü:")
    if verify_chain():
        print("❌ HATA: Manipülasyon algılanamadı.")
    else:
        print("✅ BAŞARILI: Veri bütünlüğü bozulmuş olarak algılandı.")

    print("\n4) Test sonrası eski oy geri yükleniyor...")
    ballots[1]["encrypted_vote"] = original_vote
    save_ballots(ballots)

    print("\n5) Son kontrol:")
    if verify_chain():
        print("✅ Zincir tekrar sağlam hale getirildi.")
    else:
        print("❌ Zincir geri yüklenemedi.")


if __name__ == "__main__":
    main()
