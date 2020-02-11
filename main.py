from urllib import parse
import requests
import json
import random
import time
import os
from tqdm import tqdm

# 请求url 每次请求的图片数量
URL_PARAM_RN = 30
def parse_keyword(key_word):
    '''
    将图片的关键字解析为url格式
    '''
    return parse.quote(key_word)


def get_url(key_word,pn,rn=URL_PARAM_RN):
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
        &tpltype=0'''.format(key_word,pn,rn,'' if pn/rn==1 else hex(pn)[2:])
    
    print('request_url------------------',request_url)
    return ''.join(request_url.split())


def download(key_word,image_count=25,path_prefix=''):
    '''
    key_word：关键词
    image_count:需要的数量
    '''
    headers={ "User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1" ,
    "Referer":"https://m.baidu.com/sf/vsearch?pd=image_content&word=%E7%83%A4%E9%B8%AD&tn=vsearch&atn=page"
    }
    # 创建存放的目录
    if not os.path.exists('./'+key_word):
        os.mkdir('./'+key_word)
    for i in tqdm(range(1+ image_count//URL_PARAM_RN),desc='发送请求中...'):
        request_url = get_url(key_word,(i+1)*URL_PARAM_RN)
        print('-----请求中-----------',request_url)
        response = requests.get(request_url,headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            print('-------处理返回值--------')
            # response.json() 会将结果中的json解析为字典数据
            ret_dict = response.json()
            linkData = ret_dict.get('linkData')
            for index,item in tqdm(enumerate(linkData),desc='下载图片中...'):
                image_url = item.get('hoverUrl')
                if len(image_url)==0:
                    image_url = item.get('thumbnailUrl')
                    if len(image_url) ==0:
                        image_url = item.get('objurl')
                print('-----请求图片',image_url)
                response_image = requests.get(image_url)
                if response_image.status_code==200:
                    with open('./'+key_word+'/'+str(i)+'-'+str(index)+'.jpg','wb') as f:
                        f.write(response_image.content)
                else:
                    print('请求失败----',image_url)


if __name__ == '__main__':
    download('一品豆腐',image_count=90)
