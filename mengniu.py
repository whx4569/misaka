#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : github@yuanter https://github.com/yuanter
# @Time : 2022/12/14 00:23
# -------------------------------
# cron "55 59 8 * * *" script-path=xxx.py,tag=匹配cron用
# const $ = new Env('蒙牛呛奶');
"""
蒙牛呛奶 微信小程序入口:蒙牛世界杯 抓 领奖记录请求中的 Authorisation
1. 脚本仅供学习交流使用, 请在下载后24h内删除
2. 需要第三方库 requests和pycryptodome 支持 命令行安装 pip3 install requests或pycryptodome，或者根据自己环境自行安装
3. 环境变量说明 mengniuCK(必需)  自行新建环境变量添加
    mengniuCK 为你的Authorisation值  多账号使用&或者#隔开
"""
import base64
import datetime
import hashlib
import json
import os
import random
import sys
import threading
import time

import requests
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
from tools.ql_api import get_cookie


def printf(text):
    ti = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f'[{ti}]: {text}')
    sys.stdout.flush()

def desEn(content, key):
    key = key[:8].encode('utf-8')
    content = content.encode('utf-8')
    cipher = DES.new(key=key, mode=DES.MODE_ECB)
    content = pad(content, block_size=DES.block_size, style='pkcs7')
    res = cipher.encrypt(content)
    return base64.b64encode(res)

def desDe(content, key):
    key = key[:8].encode('utf-8')
    content = base64.b64decode(content)
    cipher = DES.new(key=key, mode=DES.MODE_ECB)
    res = cipher.decrypt(content)
    res = unpad(res, DES.block_size, style='pkcs7')
    return res.decode('utf-8')

def generate_random_str(randomlength=16):
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str

def getTimestamp():
    return int(round(time.time() * 1000))

def rcape(v):
    if len(v) != 2:
        return '0'+v
    return v

def getJsonId():
    global start_time
    url = 'https://gz-cdn.xiaoyisz.com/mengniu_bainai/game_configs/prod_v1/game_configs.json?v=1670228082180'
    res = requests.get(url=url, headers=head).json()
    month = datetime.datetime.now().strftime('%m')
    day = datetime.datetime.now().strftime('%d')
    day = rcape(str(int(day) - 1))

    for item in res['activity_data']:
        result_id = item['result_id']
        result_id = result_id.replace('result_', '')
        json_id = item['json_id']
        if result_id == (month+day):
            reward_Num = item['reward_Num']
            start_time = item['start_time']
            printf(f'今日可抢牛奶数量：{reward_Num}')
            return json_id
    return ''

def getRKSign(timestamp, nonce):
    md5Str = f'clientKey={clientKey}&clientSecret={clientSecret}&nonce={nonce}&timestamp={timestamp}'
    return hashlib.md5(md5Str.encode('utf-8')).hexdigest().upper()

def getRk(domain):
    timestamp = getTimestamp()
    nonce = generate_random_str(16)
    sign = getRKSign(timestamp, nonce)
    url = f'{domain}/mengniu-world-cup/mp/api/user/baseInfo?timestamp={timestamp}&nonce={nonce}&signature={sign}'
    
    try:
        res = requests.get(url=url, headers=head).json()
        printf(res)
        return res['data']['rk']
    except Exception:
        #printf('获取账号rk失败，该token已经触发风控机制，请重新抓包获取新token')
        raise Exception('获取账号rk失败，该token已经触发风控机制，请重新抓包获取新token')
    

def getMilkSign(requestId, timestamp, rk):
    md5Str = f'requestId={requestId}&timestamp={timestamp}&key={rk}'
    return hashlib.md5(md5Str.encode('utf-8')).hexdigest()

def skillMilk(rk, jsonId):
    timestamp = getTimestamp()
    requestId = generate_random_str(32)
    nonce = generate_random_str(16)
    signature = getRKSign(timestamp, nonce)
    sign = getMilkSign(requestId, timestamp, rk)
    url = f'{domain}/mengniu-world-cup-1122{updateUrl}?timestamp={timestamp}&nonce={nonce}&signature={signature}&jsonId={jsonId}'
    head['sign'] = sign
    head['timestamp'] = str(timestamp)
    head['requestId'] = requestId
    res = requests.get(url=url, headers=head, timeout=10).text
    printf(res)
    

def isStart():
    current_time = getTimestamp()
    if current_time >= (start_time - preTime):
        return True
    else:
        return False


def start(token):
    config={
        "token": token,
        "clientKey": "FIDBFh4U65amvCDIlvE92WECR8txa48K",
        "clientSecret": "qzEKyCTxQdaquxm5u2OJKB3bVTie4f9qHTQIDTIGxCc88egeIAyJ6QXQeow8whvU",
        "updateUrl": "/mp/api/user/seckill/ghg3/dff/dd2/dsfs2/e21d/vddc",
        "threadNumber": 200,
        "preTime": 2000,
        "desKey": "pZN8^thwwfKl8^oz",
        "domain": "https://mengniu-apig.xiaoyisz.com",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.30(0x18001e31) NetType/WIFI Language/zh_CN",
        "Referer": "https://servicewechat.com/wx8e45b2134cbeddff/62/page-frame.html"
        }


    '''
    time无需管 服务器获取
    '''
    start_time = 0
    domain = config['domain']

    '''
    token是小程序包的请求头的Authorization: 
    '''
    #修改本处token的加载，优先环境，再json文件
    if token == "":
        token = config['token']
    desKey = config['desKey']
    clientKey = config['clientKey']
    clientSecret = config['clientSecret']
    updateUrl = config['updateUrl']
    '''
    请求头
    '''
    head = {
        'User-Agent': config['User-Agent'],
        'Referer': config['Referer'],
        'content-type': 'application/json',
        'Authorization': token
    }
    # print(token)
    # print(desKey)
    # print(clientKey)
    # print(clientSecret)
    # print(updateUrl)
    # print(domain)




    '''
    账号的rk 自动获取
    '''
    rk = getRk(domain)
    '''
    抢多少次最大24 多了触发风控机制 导致无法获取rk 所有接口返回{"code":500,"message":"非领奶时间"} 触发风控机制后需要更新toekn才能恢复正常
    '''
    threadNumber = config['threadNumber']
    '''
    提交几秒开枪（单位毫秒）
    如 2000 就是 8:59:58秒开枪
    '''
    preTime = config['preTime']

    rk = desDe(rk, desKey)
    jsonId = getJsonId()
    time.sleep(1)
    skillMilk(rk, jsonId)
    time.sleep(1)
    tdList = []

    for i in range(threadNumber):
        tdList.append(threading.Thread(target=skillMilk, args=(rk, jsonId)))

    while True:
        if isStart():
            for tdItem in tdList:
                try:
                    tdItem.start()
                    time.sleep(0.1)
                except Exception as e:
                    printf(f'抢奶异常：{str(e)}')
            break
        else:
            printf("等待开始...")
        time.sleep(0.1)
    #os.system('pause')




if __name__ == '__main__':
    #初始参数
    domain = ""
    token = ""
    desKey = ""
    clientKey = ""
    clientSecret = ""
    updateUrl = ""
    head = {}


    l = []
    user_map = []
    cklist = get_cookie("mengniuCK")
    for i in range(len(cklist)):
        #以#或者&亦或者换行符分割开的ck
        split1 = cklist[i].split("#")
        split2 = cklist[i].split("&")
        split3 = cklist[i].split("\n")
        if len(split1)>1:
            for j in range(len(split1)):
                user_map.append(split1[j])
        elif len(split2)>1:
            for j in range(len(split2)):
                user_map.append(split2[j])
        elif len(split3)>1:
            for j in range(len(split3)):
                user_map.append(split3[j])
        else:
            if cklist[i] != "":
                user_map.append(cklist[i])


    for i in range(len(user_map)):
        token=""
        token = user_map[i]
        print('开始执行第{}个账号：{}'.format((i+1),token))
        if token == "":
            print("当前账号未填写token 跳过")
            print("\n")
            continue
        p = threading.Thread(target=start,args=(token,))
        l.append(p)
        p.start()
        print("\n")
    for i in l:
        i.join()
