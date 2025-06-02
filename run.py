from main import *

with open('./conf/Daily_List.json', 'r', encoding='utf-8') as f:
    Daily_List = json.load(f)

num = 1

start_time = time.time()  # 记录开始时间戳

while num <= conf['device_num'] :
    Popcorn_Obtain_Num = 0
    #用户配置文件名称
    User_Name = "user-"+ str(num)
    #用户配置文件目录
    User_Path = "./user/" + User_Name +".yaml"
    #新日志文件名称
    Log_File_Name = User_Name + "-" + str(int(time.time())) + '.log'
    #新日志文件名称名称
    Log_Path = './log/' + Log_File_Name
    #读取用户配置文件
    with open(str(User_Path), 'r', encoding='utf-8') as f:
        user = yaml.load(f.read(), Loader=yaml.FullLoader)
    #确定日志格式
    log = {
        'user': "user-"+ str(num) ,
        'Get_bmh_num': 0 ,
        'Getprize': []
    }
    #除去老旧日志
    while len(user['Log_List']) >= 4:
        #待移除的日志目录
        Log_Remove_Path = './log/' + user['Log_List'][0]
        #删除用户配置文件的日志记录
        user['Log_List'].pop(0)
        #删除日志文件
        os.remove(Log_Remove_Path)
    #添加新的日志记录
    user['Log_List'].append(Log_File_Name)
    #完成活动
    response = Activities_Complete(user)
    #处理爆米花数量
    Popcorn_Obtain_Num += int(response['Popcorn_Current_Num'])
    #追加日志
    log['Getprize'] = response['result']
    #完成每日“赚爆米花”任务
    response = Daily_Complete(Daily_List, user)
    #追加爆米花数量
    Popcorn_Obtain_Num += int(response['Add_Popcorn_num'])
    #追加日志
    log['Add_Corn_num'] = response['Add_Corn_num']
    #将写入日志记录写进配置文件
    with open(User_Path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(user, f)
    #将日志写入新日志文件
    with open(Log_Path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    #循环变量加一
    num += 1

#获取结束时间戳
end_time = time.time()
#获取间隔时间
execution_time = end_time - start_time
#输出日志
print(f"代码执行耗时: {execution_time:.2f} 秒")