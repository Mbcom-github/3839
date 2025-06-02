from main import *
import time

#daily 每日必做
#ycx 更多必做
#plant 植物操作
#sign 每日登录

with open('./conf/Daily_List.json', 'r', encoding='utf-8') as f:
    Daily_List = json.load(f)

Url_Type_List = ['daily', 'ycx', 'plant', 'sign']
While_Num = 0
Daily_List_Num = len(Daily_List) - 2
while While_Num <  Daily_List_Num:

    Task_Type = Daily_List[While_Num]['Task_Type']

    Id = Daily_List[While_Num]['Task_Id']

    Post_Daily(Task_Type, Id, user)

    While_Num += 1

exit()

time.sleep(300)
while() :
    Post_Daily()

