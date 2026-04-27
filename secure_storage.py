import os
import json
from crypto_utils import encrypt_json_file, decrypt_json_file

def load_secure_json(file_path, default_data):
    if not os.path.exists(file_path):
        save_secure_json(file_path, default_data)
        return default_data

    try:
        return decrypt_json_file(file_path)
    except Exception:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

def save_secure_json(file_path, data):
    temp_path = file_path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    os.replace(temp_path, file_path)
    encrypt_json_file(file_path)
