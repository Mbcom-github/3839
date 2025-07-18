import yaml
import requests
import json
import re
import time
import random
import os
from threading import Thread
from multiprocessing import Process
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

retry_strategy = Retry(
    total=3,  # 最大重试次数
    backoff_factor=1,  # 退避因子（等待时间 = backoff_factor * (2^(重试次数-1))秒）
    status_forcelist=[500, 502, 503, 504],  # 需要重试的HTTP状态码
    allowed_methods=["POST", "GET"]  # 允许重试的HTTP方法
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

#post任务请求主函数
def Post_Activity(url, Task_Complete_Type, comm_id, Task_id, user):
    #url为目的链接，ac为执行类型，comm_id为任务id
    #该list变量容纳待执行的任务类型
    ac_list = ["completeTask"]
    #upGameTask类型的列表，用于筛选符合的类型
    upGameTask_list = ["tasktype_2", "tasktype_7", "tasktype_10", "tasktype_11", "tasktype_14", "tasktype_16", "tasktype_18"]
    r = "0." + str( time.time_ns()) + str(random.randint(100,999))
    #请求体
    payload = {
        'ac': 'getTaskPrize',
        'comm_id': int(comm_id),      
        'smdeviceid': user['smdeviceid'], #——只有兑换请求需要
        'verison': user['verison'],
        'r': r,
        'scookie': user['scookie'],
        'device': user['device'],
        'id': Task_id
    }
    #请求头
    headers = {
        'User-Agent': user['User-Agent']
    }
    response_log = []
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
        response = json.loads(session.post(url, data=payload, headers=headers).text)
        #if判断json的键值
        if response.get('info') == '已领取过奖励':
            return [{  # 返回包含错误信息的字典
                "key": "error",
                "info": "已领取过奖励",
                "detail": f"今日已领取，comm_id={comm_id}, Task_id={Task_id}"
            }]

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
        response = json.loads(session.post(url, data=payload, headers=headers).text)
        #循环变量加一
        cycle_current_num += 1
        response_log.append(response)

    return response_log
    
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
        response = session.get(i).text
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

        response = json.loads(session.post(object_web, data=payload).text)

        ac_id_list = {
            "comm_id": i,
            "ac_ids_num": response['num'],
            "ac_ids_list": tidy_ac_id(response['all']['Daily'])
        }

        ac_ids_list.append(ac_id_list)

    #结束连接池
    session.close()

    return ac_ids_list

#获取“赚爆米花”中2的“每日必做”的任务id列表
def obtain_daily_list():

    url = 'https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0'

    html = session.get(url).text

    # 正则表达式模式
    pattern = r'<div class="task-prize">(.*?)<div class="task-info">'
    blocks = re.findall(pattern, html, re.DOTALL)

    result = [{
        "Task_Type": 'DailyApp',
        "Task_Id": 5,
        "Task_Url_Type": 'daily'
    },{
        "Task_Type": "DailyGameCateJump",
        "Task_Id": 6,
        "Task_Url_Type": 'daily'
    }]

    Skip_List = ["DailyYuyueLing", 'YcxYuyueLing', 'YcxToWeiboRemind', 'YcxToWechatRemind']

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

        # 特殊处理
        if task_type in Skip_List:
            continue

        if 'Daily' in task_type:
            task_data['Task_Url_Type'] = 'daily'
        elif 'Ycx' in task_type:
            task_data['Task_Url_Type'] = 'ycx'

        result.append(task_data)

    return result

#单个“每日必做”任务完成函数
def Daily_Base_Post(Url_Type, Task_Type, id , user, while_num, while_object_num) :
    r = "0." + str( time.time_ns()) + str(random.randint(100,999))

    Base_Url = 'https://huodong3.3839.com/n/hykb/cornfarm/ajax'
 
    if Url_Type :
        Base_Url += '_'
    Url = Base_Url + Url_Type + '.php'

    Url_Type_List = ['daily', 'ycx']

    payload = {
        'id' : id ,
        'scookie': user['scookie'],
        'device': user['device'],
        'r': r
    }

    headers = {
        'User-Agent': user['User-Agent']
    }
    
    while while_num < while_object_num :

        if Url_Type in Url_Type_List:
            ac = conf[Url_Type][Task_Type][while_num]
        elif Url_Type == 'sign' and Task_Type == 'Sign':
            ac = Task_Type

            payload['smdeviceid'] = user['smdeviceid']

            payload['verison'] = user['verison']

            payload['OpenAutoSign'] = 'close'
        else :
            ac = Task_Type

        payload['ac'] = ac 
        
        if ac == 'DailyDatiAnswer' and while_num == 2:
            option = response.get('back_answer')
            if option :
                payload['option'] = option

        response = json.loads(session.post(Url, payload, headers).text)

        while_num += 1

    return response

#兑换商品基础函数
def Exchange_Base_Post(id, Exchange_Type, user):
    a = conf['exchange'][Exchange_Type]['a']

    c = conf['exchange'][Exchange_Type]['c']

    Url = 'https://shop.3839.com/index.php?c=' + c + '&a=' + a

    r = "0." + str( time.time_ns()) + str(random.randint(100,999))

    payload = {  
        'smdeviceid': user['smdeviceid'],
        'version': user['verison'],
        'r': r,
        'client': '1',
        'isIos': '0',
        'scookie': user['scookie'],
        'device': user['device'],
        'id': id
    }

    headers = {
        'User-Agent': user['User-Agent']
    }

    response = json.loads(session.post(Url, payload, headers=headers).text)

    return response

#兑换种子函数
def Exchange_Seed():
    for i in conf['exchange']:
        if i == 'share':
            break
        Exchange_Base_Post(8220, i, user)

#每日获取爆米花主函数
def Daily_Complete(Daily_List, user):
    #定义玉米增加量变量
    Add_Corn_num = 0
    #定义爆米花增加量变量
    Add_Popcorn_num = 0

    #获取每日兑换分享的奖励，共3次
    for i in range(3):
        #进行post请求
        response = Exchange_Base_Post(8220, 'share', user)
        #如果获取成功
        if response['code'] == 200 :
            #追加
            Add_Corn_num += 2
        #反之
        else :
            #推出循环
            break

    #收获
    response = Daily_Base_Post('plant', 'Harvest', '', user, 0, 1)

    #如果收获成功
    if response.get('key') == 'ok' and response.get('key'):
        #种植
        Daily_Base_Post('plant', 'plant', '', user, 0, 1)
        #兑换种子
        Exchange_Seed()
        #追加玉米增加量
        Add_Corn_num += int(response['add_corn'])
    #如果未种植
    elif str(response.get('key')) != "503":
        #种植
        response = Daily_Base_Post('plant', 'plant', '', user, 0, 1)

    #每日浇水
    response = Daily_Base_Post('sign', 'Sign', '', user, 0, 1)

    #如果浇水成功
    if response.get('key') == 'ok' :
        #追加爆米花增加量
        Add_Popcorn_num += int(response.get('add_baomihua'))

    #遍历每日任务列表来完成任务
    for i in Daily_List:
        #获取任务类别
        Task_Type = i['Task_Type']
        #获取任务id
        Id = i['Task_Id']
        #获取Url类别
        Url_Type = i['Task_Url_Type']
        #获取循环次数
        while_object_num = len(conf[Url_Type][Task_Type]) - 1
        #完成任务
        Daily_Base_Post(Url_Type, Task_Type, Id, user, 0, while_object_num)

    #等待部分计时任务，这破hykb，任务是真计时啊，还tm是服务器计时, 搁这硬等
    time.sleep(330)

    #遍历每日任务列表来获取任务奖励
    for i in Daily_List:
        #获取任务类别
        Task_Type = i['Task_Type']
        #获取任务id
        Id = i['Task_Id']
        #获取Url类别
        Url_Type = i['Task_Url_Type']
        #获取循环次数
        while_object_num = len(conf[Url_Type][Task_Type])
        #设定初始循环变量
        while_num = while_object_num - 1
        #获取植物成熟度
        response = Daily_Base_Post('', 'RereadPlant', Id, user, 0, 1)
        #赋值给变量
        Maturity = int(response['chengshoudu'])

        #如果成熟
        if Maturity == 100 :
            #收获
            response = Daily_Base_Post('plant', 'Harvest', '', user, 0, 1)
            #购买种子
            Exchange_Seed()
            #种植
            Daily_Base_Post('plant', 'plant', '', user, 0, 1)
            #追加玉米增加量
            Add_Corn_num += int(response['add_corn'])
        #如果未成熟
        else :
            #获取任务奖励
            response = Daily_Base_Post(Url_Type, Task_Type, Id, user, while_num, while_object_num)
            print(response)
            #获取爆米花增加量
            Add_Popcorn = response.get('reward_bmh_num')
            #如果奖励有爆米花
            if Add_Popcorn :
                #则追加爆米花增加量
                Add_Popcorn_num += int(Add_Popcorn)
            
    #处理日志格式
    log = {
        'Add_Popcorn_num': Add_Popcorn_num,
        'Add_Corn_num': Add_Corn_num 
    }
    #返回结果
    return log

#每日活动完成主函数
def Activities_Complete(user):
    #Post目标链接
    url = 'https://act.3839.com/n/hykb/universal/ajax.php'
    #获取结果过滤列表
    Info_List = conf['Info_List']
    #定义‘爆米花’获取数量的变量
    Popcorn_Current_Num = 0
    #定义传出结果变量
    result = []

    #遍历出所有的活动
    for i in Task_Ids_List:
        #获取comm_id
        comm_id = i['comm_id']
        #定义单个活动的日志
        current_log = {'Comm_id': comm_id, 'log': []}

        #遍历出在当前活动中的所有任务
        for y in i['ac_ids_list']:
            #获取任务id
            Task_id = y['task_id']

            #获取任务类别
            tasktype = y['type']   

            #完成单个活动中的单个任务
            response = Post_Activity(url, tasktype, comm_id, Task_id, user)

            #定义该任务日志
            result_log = {
                'response': response,
                'tasktype': tasktype,
                'Task_id': Task_id
            }

            print(response)

            #判断该任务执行结果
            response = response[-1]

            #如果不为成功
            if str(response['key']) != 'ok' :
                #如果输出非奖品且非爆米花
                if str(response.get('name')) in Info_List or response.get('key') == 'error':
                    #结束单词循环
                    continue
                #反之
                else :
                    #处理结果
                    result_log['info'] = response['info']
                    #追加日志
                    current_log['log'].append(result_log)
            #如果结果为非爆米花且为奖品
            elif str(response.get('code')) != '0' and response.get('code') is not None:
                #处理日志
                result_log['info'] = response['name']
                result_log['code'] = response['code']
                #追加日志
                current_log['log'].append(result_log)
            #排除完即为爆米花
            else :
                #处理日志
                result_log['info'] = response['name']
                #提取爆米花数额
                Popcorn_num = re.search(r'\d+$', response['name']).group()
                #追加爆米花数额
                Popcorn_Current_Num += int(Popcorn_num)

            

        #追加该次活动的日志
        result.append(current_log)

    #整理日志
    response = {
        'Popcorn_Current_Num': Popcorn_Current_Num,
        'result': result
    }
    
    #返回日志
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