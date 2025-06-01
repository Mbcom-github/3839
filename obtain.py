from main import *

with open('./conf/ac_ids.json', 'w', encoding='utf-8') as f:
    json.dump(obtain_ac_ids(obtain_comm_ids('ac_web')), f, indent=4)

with open('./conf/Daily_List.json', 'w', encoding='UTF-8') as f:
    json.dump(obtain_daily_list(), f, indent=4, ensure_ascii=False)