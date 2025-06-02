import yaml
import requests
import json
import re
import os
import time

#post任务请求主函数
def post(url, Task_Complete_Type, comm_id, Task_id, user):
    #url为目的链接，ac为执行类型，comm_id为任务id
    #该list变量容纳待执行的任务类型
    ac_list = ["completeTask"]
    #upGameTask类型的列表，用于筛选符合的类型
    upGameTask_list = ["tasktype_2", "tasktype_7", "tasktype_10", "tasktype_11", "tasktype_14", "tasktype_16", "tasktype_18"]
    #请求体
    payload = {
        'ac': 'getTaskPrize',
        'comm_id': int(comm_id),      
        #'smdeviceid': user['smdeviceid'], #——只有兑换请求需要
        'verison': user['verison'],
        'r': "0.9848751991131748",
        'scookie': user['scookie'],
        'device': user['device'],
        'id': Task_id
    }
    #请求头
    headers = {
        'User-Agent': user['User-Agent']
    }
    #判断任务类别
    if Task_Complete_Type == 'tasktype_1' :
        #更改请求顺序
        ac_list = ["share", "completeTask"]
        #加入特有的请求体
        payload['share_type'] = 'task'
        #同上
        payload['task_id'] = Task_id
    #同上
    elif Task_Complete_Type in upGameTask_list :
        #判断是否已领取
        response = json.loads(requests.post(url, data=payload, headers=headers).text)
        #if判断json的键值
        if response.get('info') == '已领取过奖励':
            return {  # 返回包含错误信息的字典
                "key": "error",
                "info": "已领取过奖励",
                "detail": f"今日已领取，comm_id={comm_id}, Task_id={Task_id}"
            }

        ac_list = ["upGameTask", "completeTask"]

        payload['task_id'] = Task_id

        payload['type'] = '6'
    #补充任务类型（两者分别为获取奖励和进行抽奖）
    ac_list = ac_list + ["getTaskPrize", "getLuckyPrize"]
    #设置循环变量
    cycle_current_num = 0
    #进入post请求循环，完成从“完成任务”到“抽取奖励”的过程
    while cycle_current_num < len(ac_list) :
        #加入必须请求体
        payload['ac'] = ac_list[cycle_current_num]
        #post请求
        response = json.loads(requests.post(url, data=payload, headers=headers).text)
        #循环变量加一
        cycle_current_num += 1

    return response
    
#整理html文本来获取comm_id
def extract_comm_ids(html):

    #html为html文本变量，一般要求为str，例：用response.text来获取的文本

    # 使用正则表达式匹配所有comm_id的值
    pattern = r'''["']https://act\.3839\.com/n/hykb/universal/index\.php\?.*?comm_id=(\d+)'''
    matches = re.findall(pattern, html)
    # 转换为整数并排序
    return sorted({int(m) for m in matches})

#获取合适comm_id列表函数
def obtain_comm_ids(ac_web):

    #ac_web为config.yaml中‘活动目录网页’的键值，默认为‘ac_web’

    #定义空变量
    comm_ids_list=[]
    #遍历任务目录网址来获取活动链接及comm_id
    for i in conf[ac_web]:
        #获取列表
        response = requests.get(i).text
        #网页提取并列表合并
        comm_ids_list=extract_comm_ids(response) + comm_ids_list
    #除重并排序
    comm_ids_list = list(set(comm_ids_list))
    return comm_ids_list

#整理html文本来获取ac_id
def tidy_ac_id(html):
    #html为含有html文本的str值
    pattern = r'''
    <div\s+class="task-btn">  # 起始标记
    (.*?)                     # 中间内容（非贪婪匹配）
    领取奖励</a></div>         # 结束标记
    '''

    json_data = []
    for match in re.finditer(pattern, html, re.DOTALL | re.VERBOSE):
        content = match.group(1)
        
        # 提取各字段
        task_id_match = re.search(r'data-task_id="(\d+)"', content)
        type_match = re.search(r'\b(tasktype_\w+)\b', content)
        complete_match = re.search(r'\b(completeTask_\d+)\b', content)
        prize_match = re.search(r'\b(getTaskPrize_\d+)\b', content)
        
        if all([task_id_match, type_match, complete_match, prize_match]):
            entry = {
                "task_id": task_id_match.group(1),
                "type": type_match.group(1),
                "complete_type": complete_match.group(1)
            }
            json_data.append(entry)

    return json_data

#遍历多个comm_id对应的ac_id列表
def obtain_ac_ids(comm_ids_list):
    #comm_ids_list为comm_id的列表
    ac_ids_list = []

    for i in comm_ids_list:
        #post请求的目的链接
        object_web = 'https://act.3839.com/n/hykb/universal/ajax.php'

        payload = {
            'ac': 'getAllTasklist',
            'comm_id': i
        }

        response = json.loads(requests.post(object_web, data=payload).text)

        ac_id_list = {
            "comm_id": i,
            "ac_ids_num": response['num'],
            "ac_ids_list": tidy_ac_id(response['all']['Daily'])
        }

        ac_ids_list.append(ac_id_list)

    return ac_ids_list

#获取“赚爆米花”中2的“每日必做”的任务id列表
def obtain_daily_list():

    url = 'https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0'

    html = requests.get(url).text

    # 正则表达式模式
    pattern = r'<div class="task-prize">(.*?)<div class="task-info">'
    blocks = re.findall(pattern, html, re.DOTALL)

    result = []

    for block in blocks:
        # 提取第一个 onclick 属性
        onclick_match = re.search(r'onclick\s*=\s*"([^"]+)"', block)
        
        if not onclick_match:
            continue
            
        onclick_value = onclick_match.group(1)
        
        # 提取函数名和任务ID
        func_match = re.search(r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\((\d+)', onclick_value)
        
        if not func_match:
            continue
            
        task_type = func_match.group(2)
        task_id = func_match.group(3)
        
        # 初始化结果字典
        task_data = {
            "Task_Type": task_type,
            "Task_Id": task_id
        }
        
        # 特殊处理 DailyYuyueLing 类型
        if task_type == "DailyYuyueLing":
            # 向前搜索第一个 data-game_id
            game_id_match = re.search(r'data-game_id\s*=\s*"(\d+)"', block[:onclick_match.start()])
            
            if game_id_match:
                task_data["Game_Id"] = game_id_match.group(1)
            else:
                # 如果在前半部分没找到，搜索整个块
                game_id_match = re.search(r'data-game_id\s*=\s*"(\d+)"', block)
                if game_id_match:
                    task_data["Game_Id"] = game_id_match.group(1)
        
        result.append(task_data)

    return result

#
def Post_Daily(Url_Type, ac, id , user) :
    
    url = 'https://huodong3.3839.com/n/hykb/cornfarm/ajax_' + Url_Type + '.php'

    payload = {
        'ac' : ac ,
        'id' : id ,
        'scookie': user['scookie'],
        'device': user['device']
    }


    headers = {
        'User-Agent': user['User-Agent']
    }

    while_num = 0

    #if Url_Type == 'daily' :
    while while_num < len(conf[ac]) :
        if ac == 'DailyDati' :
        #payload['option'] = option

        response = json.loads(requests.post(url, payload, headers))

    return response

#读取总配置文件
with open('./conf/config.yaml', 'r', encoding='utf-8') as f:
    conf = yaml.load(f.read(), Loader=yaml.FullLoader)
#读取用户文件
with open(str('./user/user-1.yaml'), 'r', encoding='utf-8') as f:
    user = yaml.load(f.read(), Loader=yaml.FullLoader)
#读取活动任务目录文件
with open(str('./conf/ac_ids.json'), 'r', encoding='utf-8') as f:
    Task_Ids_List = json.load(f)