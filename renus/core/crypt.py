import base64
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
import os


def pad(s):
    block_size = 16
    remainder = len(s) % block_size
    padding_needed = block_size - remainder
    return s + padding_needed * ' '


def unpad(s):
    return s.rstrip()


def encrypt(plain_text, password):
    salt = os.urandom(AES.block_size)

    iv = Random.new().read(AES.block_size)

    private_key = hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)

    padded_text = pad(plain_text)

    cipher_config = AES.new(private_key, AES.MODE_CBC, iv)

    return base64.b64encode({
        'cipher_text': cipher_config.encrypt(padded_text),
        'salt': salt,
        'iv': iv
    })


def decrypt(enc_dict, password):
    dec_dict=base64.b64decode(enc_dict)
    salt = dec_dict['salt']
    enc = dec_dict['cipher_text']
    iv = dec_dict['iv']

    private_key = hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)

    cipher = AES.new(private_key, AES.MODE_CBC, iv)

    decrypted = cipher.decrypt(enc)

    original = unpad(decrypted)

    return original
