from urllib import parse
import requests
import json
import random
import time
import os
from tqdm import tqdm
import pandas as pd
from pprint import pprint
from queue import Queue
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
# 请求url 每次请求的图片数量
URL_PARAM_RN = 50
# 启用进程数量
MAX_PROCESS_NUMBER=10
MULTIKEY=False
SAVE_PAHT_PREFIX='/Volumes/Data3/'

def parse_excel(excel_path,sheet_name='',sheet_index=0):
    '''
    从excel表格中获取需要爬取的图片信息
    excel_path:指定excel文件的路径
    sheet_name:指定表单名
    sheet_name:指定表单索引
    默认读取excel中的第一个表单，可以通过sheet_name或者sheet_index来指定
    '''
    dataframe = pd.read_excel(excel_path,sheet_name=sheet_name if sheet_name!='' else sheet_index)
    result=list()
    for indexs in dataframe.index:
        result.append(list(dataframe.loc[indexs]))
    return result


def parse_keyword(key_word):
    '''
    将图片的关键字解析为url格式
    '''
    return parse.quote(key_word)


def get_url(key_word, pn, rn=URL_PARAM_RN):
    '''
    搜狗，360
    https://pic.sogou.com/pics?query=%9F%68%E2%C6%E2%BD+%CE%F7%B2%CD&mode=1&start=288&reqType=ajax&reqFrom=result&tn=0
    '''
    key_word = parse_keyword(key_word)
    request_url = '''https://m.baidu.com/sf/vsearch/image/search/wisesearchresult?
        tn=wisejsonala
        &ie=utf-8
        &fromsf=1
        &word={}
        &pn={}
        &rn={}
        &gsm={}
        &prefresh=undefined
        &searchtype=0
        &fromfilter=0
        &tpltype=0'''.format(key_word, pn, rn, '' if pn/rn == 1 else hex(pn)[2:])

    print('request_url------------------', request_url)
    return ''.join(request_url.split())


def downloader(key_word, image_count, path_prefix):
    '''
    key_word：关键词
    image_count:需要的数量
    path_prefix:若为None,使用key_word创建一级目录，若不为空，将文件保存在./path_prefix/key_word/
    '''
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
               "Referer": "https://m.baidu.com/sf/vsearch?pd=image_content&word=%E7%83%A4%E9%B8%AD&tn=vsearch&atn=page"
               }
    
    # 创建存放的目录
    save_path = ''
    if path_prefix=='None':
        save_path=SAVE_PAHT_PREFIX+key_word
        if not os.path.exists(save_path):
            os.mkdir(save_path)
    else:
        save_path=SAVE_PAHT_PREFIX+path_prefix+'/'+key_word
        if not os.path.exists(save_path):
            os.makedirs(save_path)

    for i in tqdm(range(1 + image_count//URL_PARAM_RN), desc='发送请求中...'):
        # 是否将 path_prefix加入到关键词中
        if MULTIKEY:
            request_url = get_url(key_word+' ' + path_prefix, (i+1)*URL_PARAM_RN)
        else:
            request_url = get_url(key_word, (i+1)*URL_PARAM_RN)
        # print('-----请求中-----------', request_url)
        response = requests.get(request_url, headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            # print('-------处理返回值--------')
            # response.json() 会将结果中的json解析为字典数据
            ret_dict = response.json()
            linkData = ret_dict.get('linkData')
            for index, item in tqdm(enumerate(linkData), desc='下载图片中...'):
                image_url = item.get('hoverUrl')
                if len(image_url) == 0:
                    image_url = item.get('thumbnailUrl')
                    if len(image_url) == 0:
                        image_url = item.get('objurl')
                # print('-----请求图片', image_url)
                response_image = requests.get(image_url)
                if response_image.status_code == 200:
                    with open(save_path+'/'+str(i)+'-'+str(index)+'.jpg', 'wb') as f:
                        f.write(response_image.content)
                else:
                    print('请求失败----', image_url)


if __name__ == '__main__':
    # items = ['鱼香肉丝',
    #          '宫保鸡丁',
    #          '水煮鱼',
    #          '水煮肉片',
    #          '夫妻肺片',
    #          '辣子鸡丁',
    #          '麻婆豆腐',
    #          '回锅肉',
    #          '东坡肘子',
    #          '辣子鸡',
    #          ]
    # for name in items:
    #     downloader('川菜/'+name, image_count=500)
    crawl_info = parse_excel('./data.xlsx',sheet_name='杂类')
    # print('-------------')
    # print(crawl_info[0][1])

    # 创建进程池
    # po = multiprocessing.Pool(MAX_PROCESS_NUMBER)
    # while(len(crawl_info)!=0):
    #     po.apply_async(downloader, tuple(crawl_info.pop()))

    # print("-----start-----")
    # po.close() # 关闭进程池，关闭后po不再接收新的请求
    # po.join() # 等待po中所有子进程执行完成，必须放在close语句之后
    # print("-----end-----")
    future_list = list()
    with ProcessPoolExecutor(max_workers=MAX_PROCESS_NUMBER) as executor:
        while(len(crawl_info)!=0):
           future_list.append(executor.submit(downloader,*crawl_info.pop())) 
        for res in tqdm(as_completed(future_list),desc='下载图片中...'): #这个futrure_list是你future对象的列表
            print(res.result())  





