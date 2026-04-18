from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import os
import base64

PRIVATE_KEY_FILE = "keys/private_key.pem"
PUBLIC_KEY_FILE = "keys/public_key.pem"


def ensure_keys_folder():
    os.makedirs("keys", exist_ok=True)


def generate_keys():
    ensure_keys_folder()

    if os.path.exists(PRIVATE_KEY_FILE) and os.path.exists(PUBLIC_KEY_FILE):
        print("Anahtarlar zaten mevcut.")
        return

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()

    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
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
        return serialization.load_pem_private_key(f.read(), password=None)


def encrypt_vote(vote_text):
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


def decrypt_vote(encrypted_vote_b64):
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


if __name__ == "__main__":
    generate_keys()

    test_vote = "A Partisi"
    encrypted_vote = encrypt_vote(test_vote)
    decrypted_vote = decrypt_vote(encrypted_vote)

    print("Orijinal Oy:", test_vote)
    print("Şifreli Oy:", encrypted_vote)
    print("Çözülmüş Oy:", decrypted_vote)
