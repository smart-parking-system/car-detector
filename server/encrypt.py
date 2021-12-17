import base64
from Crypto.Cipher import AES

class Encrypt:
    BS = 16

    def __init__(self, iv: str, key: str):
        self.key = bytes(key, 'utf-8')
        self.iv = bytes(iv, 'utf-8')

    def encrypt(self, data: str) -> str:
        data = Encrypt.pad(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(cipher.encrypt(data))

    def decrypt(self, data: str) -> str:
        data = base64.b64decode(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return Encrypt.unpad(cipher.decrypt(data)).decode('utf8')

    @staticmethod
    def pad(s: str) -> str:
      return bytes(s + (Encrypt.BS - len(s) % Encrypt.BS) * chr(Encrypt.BS - len(s) % Encrypt.BS), 'utf-8')

    @staticmethod
    def unpad(s: str) -> str:
      return s[0:-ord(s[-1:])]

