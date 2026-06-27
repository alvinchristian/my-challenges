import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# --- Configuration ---
# This KEY MUST be the exact 32-byte key used by the C utility.
# 0x2d, 0xd6, 0x15, 0x89, 0xf5, 0xdd, 0x73, 0xe2, 0x30, 0x89, 0xb0, 0xb2, 0xac, 0x0a, 0xf4, 0x24, 0x9c, 0x48, 0xc9, 0x61, 0x5e, 0xe9, 0xbb, 0x08, 0x2f, 0x58, 0x0e, 0x7a, 0xec, 0xf9, 0xf7, 0xf1
KEY = b'\x2d\xd6\x15\x89\xf5\xdd\x73\xe2\x30\x89\xb0\xb2\xac\x0a\xf4\x24\x9c\x48\xc9\x61\x5e\xe9\xbb\x08\x2f\x58\x0e\x7a\xec\xf9\xf7\xf1'
IV_SIZE = 16
EXTENSION = '.enc'
# ---------------------

def decrypt_file(encrypted_filepath: Path) -> bool:
    """Reads encrypted file, extracts IV, decrypts, unpads, and writes the original file."""
    try:
        with open(encrypted_filepath, 'rb') as f:
            encrypted_data = f.read()

        if len(encrypted_data) < IV_SIZE:
            # File too small to contain IV
            return False

        # 1. Extract IV (last 16 bytes) and Ciphertext (everything before the IV)
        iv = encrypted_data[-IV_SIZE:]
        ciphertext = encrypted_data[:-IV_SIZE]
        
        # 2. Setup Decryptor (AES-256-CBC)
        cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # 3. Decrypt
        decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # 4. Unpad (PKCS#7 is automatically handled by the C utility, so we unpad it here)
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

        # 5. Determine output filename (remove .netsus extension)
        output_filepath = encrypted_filepath.with_suffix('').name

        # 6. Write decrypted data
        with open(output_filepath, 'wb') as f:
            f.write(decrypted_data)
        
        # 7. Delete encrypted file upon successful decryption
        os.remove(encrypted_filepath)

        return True

    except Exception:
        # Fail silently if anything goes wrong during file operation or decryption
        return False


def main():
    
    current_dir = Path('.')
    
    # Iterate over all files in the current directory
    for filepath in current_dir.iterdir():
        if filepath.is_file() and filepath.name.endswith(EXTENSION):
            decrypt_file(filepath)

if __name__ == "__main__":
    main()
