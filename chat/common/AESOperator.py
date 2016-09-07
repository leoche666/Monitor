from Crypto.Cipher import AES
import base64

BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-ord(s[-1])]

class AESOperator(object):
    def __init__(self,key="a05f9ac8e35d9f32",iv="abcdefghijklmnop"):
        self.key=key
        self.iv=iv
    
    def setKeyIv(self,key,iv):
        self.Key,self.iv = key,iv
          
    def encrypt(self,bytesStr):
        #base64
        encodeBase64 = base64.b64encode(bytesStr)
        
        #PKCS5Padding->AES,CBC 
        generator = AES.new(self.key, AES.MODE_CBC, self.iv)
        crypt = generator.encrypt(pad(encodeBase64))  
        
        #base64
        return base64.b64encode(crypt)
        
        
    def decrypt(self,bytesStr):
        #base64
        decodeBase64 = base64.b64decode(bytesStr)
        
        #PKCS5Padding->AES,CBC
        generator = AES.new(self.key, AES.MODE_CBC, self.iv)
        crypt = generator.decrypt(decodeBase64) 
        unCrypt = unpad(crypt)
    
        #base64
        return base64.b64decode(unCrypt)