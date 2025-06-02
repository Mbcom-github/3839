from main import *
import os
import time

url = 'https://act.3839.com/n/hykb/universal/ajax.php'

num = 1 

start_time = time.time()  # 记录开始时间戳

Info_List = ['谢谢参与', '已领取过奖励', '你还没有抽奖次数哦，快去完成任务获得次数吧~']

while num <= conf['device_num'] :
    baomihua = 0
    #用户配置文件目录
    User_Name = "user-"+ str(num)

    User_Path = "./user/" + User_Name +".yaml"

    Log_File_Name = User_Name + "-" + str(int(time.time())) + '.log'

    Log_Path = './log/' + Log_File_Name

    #读取用户配置文件
    with open(str(User_Path), 'r', encoding='utf-8') as f:
        user = yaml.load(f.read(), Loader=yaml.FullLoader)

    log = {
        'user': "user-"+ str(num) ,
        'Get_bmh_num': 0 ,
        'Getprize': []
    }

    while len(user['Log_List']) >= 4:

        Log_Remove_Path = './log/' + user['Log_List'][0]

        user['Log_List'].pop(0)

        os.remove(Log_Remove_Path)

    for i in Task_Ids_List:

        comm_id = i['comm_id']

        current_log = {'Comm_id': comm_id, 'log': []}
        
        for y in i['ac_ids_list']:

            Task_id = y['task_id']

            tasktype = y['type']

            result = Post_Activity(url, tasktype, comm_id, Task_id, user)

            result_log = {
                'Task_id': Task_id
            }

            if str(result['key']) != 'ok' :
                result_log['info'] = result['info']
                current_log['log'].append(result_log)
            elif str(result.get('code')) != '0' and result.get('code') is not None:
                result_log['info'] = result['name']
                result_log['code'] = result['code']
                current_log['log'].append(result_log)
            else :
                result_log['info'] = result['name']
                if str(result['name']) not in Info_List:
                    bmh_num = re.search(r'\d+$', result['name']).group()
                    baomihua += int(bmh_num)

        log['Getprize'].append(current_log)

    log['Get_bmh_num'] = baomihua
    
    user['Log_List'].append(Log_File_Name)

    with open(User_Path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(user, f)

    with open(Log_Path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    num += 1

end_time = time.time()     # 记录结束时间戳
execution_time = end_time - start_time
print(f"代码执行耗时: {execution_time:.2f} 秒")