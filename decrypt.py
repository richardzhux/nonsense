import hashlib

def decrypt_key_with_keyboard_shift(encrypted_key):
    """Decrypts the key by reversing the keyboard shift."""
    keyboard_rows = [
        "1234567890",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm"
    ]
    
    reverse_mapping = {}
    for row in keyboard_rows:
        for i in range(len(row)):
            reverse_mapping[row[i]] = row[(i - 1) % len(row)]
    
    decrypted_key = []
    for char in encrypted_key:
        if char.lower() in reverse_mapping:
            decrypted_char = reverse_mapping[char.lower()]
            decrypted_key.append(decrypted_char.upper() if char.isupper() else decrypted_char)
        else:
            decrypted_key.append(char)
    
    return ''.join(decrypted_key)


def validate_hash(input_text, salt, hash_output):
    """Validates the hash by recomputing it using the same salt."""
    combined = bytes.fromhex(salt) + input_text.encode('utf-8')
    recomputed_hash = hashlib.sha256(combined).hexdigest()
    return recomputed_hash == hash_output


def main():
    # Data you share with your friend
    encrypted_message = input("Enter the encrypted message (Hash): ")
    salt = input("Enter the salt: ")
    encrypted_key = input("Enter the encrypted symmetric key (Shifted): ")
    
    # Friend decrypts the symmetric key
    decrypted_key = decrypt_key_with_keyboard_shift(encrypted_key)
    print(f"Decrypted Symmetric Key: {decrypted_key}")
    
    # Friend can try validating the original message
    input_text = input("Enter the original message for validation: ")
    is_valid = validate_hash(input_text, salt, encrypted_message)
    print(f"Validation Result: {'Success! Original message verified.' if is_valid else 'Failed! Message does not match.'}")

if __name__ == "__main__":
    main()
