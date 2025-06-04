import hashlib
import os
import random
import string


def generate_hash(input_text, salt_length=16):
    """Generates a random hash using SHA-256 with a salt."""
    # Generate a random salt
    salt = os.urandom(salt_length)
    # Combine input text with salt
    combined = salt + input_text.encode('utf-8')
    # Create a SHA-256 hash
    hash_output = hashlib.sha256(combined).hexdigest()
    return hash_output, salt.hex()


def encrypt_key_with_keyboard_shift(key):
    """Encrypts the key by shifting each letter/number to the right on the keyboard."""
    keyboard_rows = [
        "1234567890",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm"
    ]
    
    # Build a mapping for shifting to the right
    mapping = {}
    for row in keyboard_rows:
        for i in range(len(row)):
            mapping[row[i]] = row[(i + 1) % len(row)]  # Wrap around to the beginning of the row
    
    encrypted_key = []
    for char in key:
        if char.lower() in mapping:
            encrypted_char = mapping[char.lower()]
            encrypted_key.append(encrypted_char.upper() if char.isupper() else encrypted_char)
        else:
            # Leave non-alphanumeric characters unchanged
            encrypted_key.append(char)
    
    return ''.join(encrypted_key)


def decrypt_key_with_keyboard_shift(encrypted_key):
    """Decrypts the key by reversing the keyboard shift."""
    keyboard_rows = [
        "1234567890",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm"
    ]
    
    # Build a reverse mapping for shifting to the left
    reverse_mapping = {}
    for row in keyboard_rows:
        for i in range(len(row)):
            reverse_mapping[row[i]] = row[(i - 1) % len(row)]  # Wrap around to the end of the row
    
    decrypted_key = []
    for char in encrypted_key:
        if char.lower() in reverse_mapping:
            decrypted_char = reverse_mapping[char.lower()]
            decrypted_key.append(decrypted_char.upper() if char.isupper() else decrypted_char)
        else:
            # Leave non-alphanumeric characters unchanged
            decrypted_key.append(char)
    
    return ''.join(decrypted_key)

def validate_hash(input_text, salt, hash_output):
    """Validates the hash by recomputing it using the same salt."""
    combined = bytes.fromhex(salt) + input_text.encode('utf-8')
    recomputed_hash = hashlib.sha256(combined).hexdigest()
    return recomputed_hash == hash_output

def main():
    # Input message
    input_text = input("Enter the message to encrypt: ")
    
    # Step 1: Generate hash (encrypted message) and a salt
    hash_output, salt = generate_hash(input_text)
    print(f"Encrypted Message (Hash): {hash_output}")
    print(f"Salt: {salt}")
    
    # Step 2: Generate a random symmetric key
    symmetric_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    # print(f"Original Symmetric Key: {symmetric_key}")
    
    # Step 3: Encrypt the symmetric key using keyboard shift
    encrypted_symmetric_key = encrypt_key_with_keyboard_shift(symmetric_key)
    print(f"Encrypted Symmetric Key (Shifted): {encrypted_symmetric_key}")
    
    # Step 4: Decrypt the symmetric key using reverse keyboard shift
    decrypted_symmetric_key = decrypt_key_with_keyboard_shift(encrypted_symmetric_key)
    # print(f"Decrypted Symmetric Key: {decrypted_symmetric_key}")
    
    # Validation
    assert symmetric_key == decrypted_symmetric_key, "Key decryption failed!"
    # print("Key encryption and decryption validated successfully.")

    is_valid = validate_hash(input_text, salt, hash_output)
    print(f"Decrypted Original Message: {input_text if is_valid else 'Validation Failed!'}")

if __name__ == "__main__":
    main()




