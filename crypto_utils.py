import os
import base64
import hashlib
import hmac
import json

from dotenv import load_dotenv

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

load_dotenv()

PRIVATE_KEY_FILE = "keys/private_key.pem"
PUBLIC_KEY_FILE = "keys/public_key.pem"


# =========================
# KLASÖR / ANAHTAR AYARLARI
# =========================
def ensure_keys_folder() -> None:
    os.makedirs("keys", exist_ok=True)


def _get_private_key_password() -> bytes:
    password = os.getenv("PRIVATE_KEY_PASSWORD")

    if not password:
        raise ValueError("PRIVATE_KEY_PASSWORD .env dosyasında tanımlı değil.")

    if len(password) < 8:
        raise ValueError("PRIVATE_KEY_PASSWORD en az 8 karakter olmalıdır.")

    return password.encode("utf-8")


# =========================
# RSA ANAHTAR ÜRETİMİ
# =========================
def generate_keys() -> None:
    ensure_keys_folder()

    if os.path.exists(PRIVATE_KEY_FILE) and os.path.exists(PUBLIC_KEY_FILE):
        print("Anahtarlar zaten mevcut.")
        return

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()
    private_key_password = _get_private_key_password()

    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    private_key_password
                )
            )
        )

    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print("RSA anahtarları üretildi.")


def load_public_key():
    with open(PUBLIC_KEY_FILE, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        key_data = f.read()

    password = _get_private_key_password()

    return serialization.load_pem_private_key(
        key_data,
        password=password
    )


# =========================
# RSA OY ŞİFRELEME
# =========================
def encrypt_vote(vote_text: str) -> str:
    public_key = load_public_key()

    encrypted = public_key.encrypt(
        vote_text.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_vote(encrypted_vote_b64: str) -> str:
    private_key = load_private_key()

    encrypted_bytes = base64.b64decode(
        encrypted_vote_b64.encode("utf-8")
    )

    decrypted = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted.decode("utf-8")


# =========================
# AES / FERNET DOSYA ŞİFRELEME
# =========================
def get_fernet_key() -> bytes:
    aes_key = os.getenv("AES_KEY")

    if not aes_key:
        raise ValueError("AES_KEY .env dosyasında tanımlı değil.")

    aes_key = aes_key.strip()

    if len(aes_key) not in (16, 24, 32):
        raise ValueError("AES_KEY 16, 24 veya 32 karakter olmalıdır.")

    key = hashlib.sha256(aes_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_json_file(file_path: str) -> None:
    """
    Verilen JSON dosyasının içeriğini AES tabanlı Fernet ile şifreler.
    Dosya adı aynı kalır, içerik okunamaz hale gelir.
    """
    if not os.path.exists(file_path):
        return

    with open(file_path, "rb") as f:
        data = f.read()

    # Dosya zaten şifreliyse tekrar şifreleme yapma
    if data.startswith(b"gAAAAA"):
        return

    fernet = Fernet(get_fernet_key())
    encrypted_data = fernet.encrypt(data)

    with open(file_path, "wb") as f:
        f.write(encrypted_data)


def decrypt_json_file(file_path: str):
    """
    AES ile şifrelenmiş JSON dosyasını çözer ve Python verisi olarak döndürür.
    """
    if not os.path.exists(file_path):
        return None

    with open(file_path, "rb") as f:
        encrypted_data = f.read()

    fernet = Fernet(get_fernet_key())
    decrypted_data = fernet.decrypt(encrypted_data)

    return json.loads(decrypted_data.decode("utf-8"))


# Eski isimlerle uyumluluk için
def encrypt_file(input_path: str, output_path: str = None) -> None:
    if output_path is None or output_path == input_path:
        encrypt_json_file(input_path)
        return

    with open(input_path, "rb") as f:
        data = f.read()

    fernet = Fernet(get_fernet_key())
    encrypted_data = fernet.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(encrypted_data)


def decrypt_file_to_bytes(input_path: str) -> bytes:
    with open(input_path, "rb") as f:
        encrypted_data = f.read()

    fernet = Fernet(get_fernet_key())
    return fernet.decrypt(encrypted_data)


# =========================
# HASH İŞLEMLERİ
# =========================
def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pbkdf2_hash(password: str, salt: bytes, iterations: int = 200_000) -> str:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )

    derived_key = kdf.derive(password.encode("utf-8"))
    return base64.b64encode(derived_key).decode("utf-8")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 200_000
    password_hash = _pbkdf2_hash(password, salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("utf-8")

    return f"pbkdf2_sha256${iterations}${salt_b64}${password_hash}"


def verify_text_hash(text: str, stored_hash: str) -> bool:
    """
    Yeni format:
    pbkdf2_sha256$iterations$salt$hash

    Eski format:
    düz SHA-256 hex
    """
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations_str, salt_b64, expected_hash = stored_hash.split("$", 3)
            iterations = int(iterations_str)
            salt = base64.b64decode(salt_b64.encode("utf-8"))

            calculated_hash = _pbkdf2_hash(text, salt, iterations)
            return hmac.compare_digest(calculated_hash, expected_hash)

        except Exception:
            return False

    legacy_hash = hash_text(text)
    return hmac.compare_digest(legacy_hash, stored_hash)


# =========================
# TEST
# =========================
if __name__ == "__main__":
    generate_keys()

    test_vote = "A Partisi"
    encrypted_vote = encrypt_vote(test_vote)
    decrypted_vote = decrypt_vote(encrypted_vote)

    print("Orijinal Oy:", test_vote)
    print("Şifreli Oy:", encrypted_vote)
    print("Çözülmüş Oy:", decrypted_vote)

    test_password = "12345"
    hashed_password = hash_password(test_password)

    print("Test Şifre Hash:", hashed_password)
    print("Doğrulama:", verify_text_hash("12345", hashed_password))
