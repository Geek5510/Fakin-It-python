from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5, AES
from hashlib import sha256
from base64 import b64encode, b64decode
from Cryptodome.Random import get_random_bytes, new as Random

"""File for encrypted Communication used by both client and server"""


class RSACipher:
    """
        Class for RSA (Asymmetric) decryption and key generation
    """
    def __init__(self):
        self.key = RSA.generate(1024)  # RSA Key
        self.rsa_decryption_cipher = PKCS1_v1_5.new(self.key)  # A decryption cipher object used to decrypt

    def decrypt(self, data):
        """
        Decrypts data using local private key
        :param data: Data to decrypt
        :return: Decrypted data
        """
        ciphertext = b64decode(data)
        plaintext = self.rsa_decryption_cipher.decrypt(ciphertext, 16)
        return b64decode(plaintext)


def RSA_encrypt(data, key):
    """
    Method to encrypt for RSA using the other side's public key
    :param data: Data to encrypt
    :param key: Public key of other side
    :return: Cipher text generated
    """
    plaintext = b64encode(data)
    other_key = RSA.importKey(key)  # Importing other side's key
    # Encrypting the data
    rsa_encryption_cipher = PKCS1_v1_5.new(other_key)
    ciphertext = rsa_encryption_cipher.encrypt(plaintext)
    return b64encode(ciphertext)


def gen_AES_key():
    """
    Returns random key for AES encryption
    """
    return get_random_bytes(24)


class AESCipher(object):
    """
    Class for AES (Symmetric) encryption and decryption
    """
    def __init__(self, key):
        """
        :param key: AES key shared by both sides
        """
        self.bs = AES.block_size
        self.key = key

    def encrypt(self, raw):
        """
        Encrypts data
        :param raw: Raw data to encrypt
        :return: Ciphertext encrypted using stored key
        """
        # Padding data
        raw = self._pad(raw)
        hashed_key = sha256(self.key).digest()  # Hashing key using sha256 in order to create fixed length key
        # Encrypting data
        iv = Random().read(AES.block_size)
        cipher = AES.new(hashed_key, AES.MODE_CBC, iv)
        return b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        """
        Decrypt data
        :param enc: Encrypted data to decrypt
        :return: plain decrypted using stored key
        """
        enc = b64decode(enc)
        hashed_key = sha256(self.key).digest()  # Hashing key using sha256 in order to create fixed length key
        # Decrypting data
        iv = enc[:AES.block_size]
        cipher = AES.new(hashed_key, AES.MODE_CBC, iv)
        # Unpadding and returning data
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        """
        Internal method, pads string for encryption
        :param s: String to pad
        :return: Padded string
        """
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        """
        Internal method, unpads string gets called after decryption
        :param s: String to unpad
        :return: Unpadded string
        """
        return s[:-ord(s[len(s)-1:])]


if __name__ == "__main__":
    # Simulates communication between client and server in project, client has RSA and sends his public key to server,
    # the server uses the public key to encrypt a symmetric key for AES encryption and sends it to the client
    # client decodes the key and both sides use it for further communications
    client_RSA = RSACipher()
    server_AES = AESCipher(gen_AES_key())

    client_public = client_RSA.key.publickey().exportKey()
    # ... Sending client public key to server ...
    # Server encodes random generated key and sends to client
    hidden = RSA_encrypt(server_AES.key, client_public)
    # Clients decodes key now server and client have the same key
    decoded = client_RSA.decrypt(hidden)

    client_AES = AESCipher(decoded)

    msg = server_AES.encrypt("Hold up the amount of fingers, that represents how handy you consider yourself around the house.")
    print(len(msg))
    recv = client_AES.decrypt(msg).decode()
    print(recv)
