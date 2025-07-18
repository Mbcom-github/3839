import hmac
import random
from urllib.parse import quote
from main import *
for i in range(8):
    print(random.randint(10,99))

print(str(time.time_ns() // 10) + str(random.randint(10,99)) )
exit()


def generate_signature(secret, params):
    sorted_params = "&".join(f"{k}={v}" for k,v in sorted(params.items()))
    return hmac.new(secret.encode(), sorted_params.encode(), 'sha256').hexdigest()

# 测试密钥有效性
test_params = {"action":"getSystemInfo", "timestamp":"1672531200"}
signature = generate_signature("au5zknkha0wkb3dqggsdedhko7nlion6", test_params)
print(signature)
