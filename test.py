from main import *

#daily 每日必做
#ycx 更多必做
#plant 植物操作
#sign 每日登录

with open('./conf/Daily_List.json', 'r', encoding='utf-8') as f:
    Daily_List = json.load(f)

Daily_Complete(Daily_List, user)