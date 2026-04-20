from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

import os
import base64
import hashlib
import hmac

load_dotenv()

PRIVATE_KEY_FILE = "keys/private_key.pem"
PUBLIC_KEY_FILE = "keys/public_key.pem"


def ensure_keys_folder() -> None:
    os.makedirs("keys", exist_ok=True)


def _get_private_key_password() -> bytes:
    password = os.getenv("PRIVATE_KEY_PASSWORD")
    if not password:
        raise ValueError("PRIVATE_KEY_PASSWORD .env dosyasında tanımlı değil.")
    if len(password) < 8:
        raise ValueError("PRIVATE_KEY_PASSWORD en az 8 karakter olmalıdır.")
    return password.encode("utf-8")


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
                encryption_algorithm=serialization.BestAvailableEncryption(private_key_password)
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

    try:
        password = _get_private_key_password()
        return serialization.load_pem_private_key(key_data, password=password)
    except Exception:
        pass

    try:
        return serialization.load_pem_private_key(key_data, password=None)
    except Exception as e:
        raise ValueError(f"Private key yüklenemedi: {e}")

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
    encrypted_bytes = base64.b64decode(encrypted_vote_b64.encode("utf-8"))
    decrypted = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted.decode("utf-8")


def get_aes_key() -> bytes:
    key = os.getenv("AES_KEY")
    if not key:
        raise ValueError("AES_KEY .env dosyasında tanımlı değil.")

    key = key.strip()

    if len(key) not in (16, 24, 32):
        raise ValueError("AES_KEY 16, 24 veya 32 karakter olmalıdır.")

    return key.encode("utf-8")


def encrypt_file(input_path: str, output_path: str) -> None:
    key = get_aes_key()
    iv = os.urandom(16)

    with open(input_path, "rb") as f:
        data = f.read()

    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    with open(output_path, "wb") as f:
        f.write(iv + encrypted_data)

    print("Dosya AES ile şifrelendi.")


def decrypt_file(input_path: str, output_path: str) -> None:
    data = decrypt_file_to_bytes(input_path)

    with open(output_path, "wb") as f:
        f.write(data)

    print("AES şifreli dosya çözüldü.")


def decrypt_file_to_bytes(input_path: str) -> bytes:
    key = get_aes_key()

    with open(input_path, "rb") as f:
        encrypted_data = f.read()

    if len(encrypted_data) < 16:
        raise ValueError("Şifreli dosya geçersiz veya bozuk.")

    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = sym_padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data


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
    Geriye dönük uyumluluk:
    - Yeni format: pbkdf2_sha256$iterations$salt$hash
    - Eski format: düz sha256 hex
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

    # Eski sha256 formatı için uyumluluk
    legacy_hash = hash_text(text)
    return hmac.compare_digest(legacy_hash, stored_hash)


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
