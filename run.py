from main import *

with open('./conf/Daily_List.json', 'r', encoding='utf-8') as f:
    Daily_List = json.load(f)

if __name__ == '__main__':

    Thread_List = []

    start_time = time.time()  # 记录开始时间戳

    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交所有任务
        futures = []
        for User_Num in range(1, conf['device_num'] + 1):
            future = executor.submit(run, User_Num, "Daily_List")
            futures.append(future)
        
        # 等待所有任务完成
        for future in futures:
            future.result()

    #结束连接池
    session.close()

    #获取结束时间戳
    end_time = time.time()
    #获取间隔时间
    execution_time = end_time - start_time
    #输出日志
    print(f"代码执行耗时: {execution_time:.2f} 秒")