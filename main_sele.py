from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests
import pandas as pd
from tqdm import tqdm
import multiprocessing
import os
from selenium.webdriver.chrome.options import Options
'''
必应版本
'''
# 网页中最后已张图片的序号
XPATH_IMG_NUM_EXPRESSION = '//*[@id="mmComponent_images_1"]/ul[last()]/li[last()]'
# 最大图片下载线程数
MAX_THREAD_NUMBER=5
# 最大浏览器进程数
MAX_PROCESS_NUMBER=5


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

def request_handler(url,save_path,index):
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1" }
    response_image = requests.get(url,headers=headers)
    print('---下载----------',url)
    if response_image.status_code == 200:
        with open(save_path+'/'+str(index)+'.jpg', 'wb') as f:
            f.write(response_image.content)
        return save_path+str(index)+ 'finished!!'
    else:
        print('请求失败----', url)

def thread_handler(imageurl_list,key_word,path_prefix):
    '''
    图片多线程下载器
    '''
    print('------------------进入thread_handler')
    # 保存目录
    save_path=''
    if path_prefix=='None':
        save_path='./'+key_word
        if not os.path.exists(save_path):
            os.mkdir(save_path)
    else:
        save_path='./'+path_prefix+'/'+key_word
        if not os.path.exists(save_path):
            os.makedirs(save_path)
    print('------------------请求')
    # for index,url in enumerate(imageurl_list):
    #     request_handler(url,save_path,index)
    # 多线程下载
    futrue_list=list()
    with ThreadPoolExecutor(max_workers=MAX_THREAD_NUMBER) as executor:
        for index,url in enumerate(imageurl_list):
            futrue_list.append(executor.submit(request_handler,url,save_path,index))
    for res in tqdm(as_completed(futrue_list),desc='下载图片中...'): #这个futrure_list是你future对象的列表
        print(res.result())  

def downloader(key_word, image_count, path_prefix):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')#解决DevToolsActivePort文件不存在的报错
    chrome_options.add_argument('--disable-gpu') #谷歌文档提到需要加上这个属性来规避bug
    chrome_options.add_argument('--headless') #浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
    chrome_options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" #手动指定使用的浏览器位置
    browser = webdriver.Chrome(chrome_options=chrome_options)
    url='https://cn.bing.com/images/trending?FORM=BESBTB&ensearch=1'
    browser.get(url)
    browser.find_element_by_id("sb_form_q").send_keys(key_word)
    browser.find_element_by_id("sb_go_par").click()

    '''
    div元素  id属性值为mmComponent_images_1_exp
    当元素的class属性名为 expandButton txtaft active 加载完成，
    当class 值为 expandButton txtaft loading 加载中
    当 class属性值中包含 disabled 已加载到底部
    '''
    loading_elem = browser.find_element_by_id("mmComponent_images_1_exp")

    # 完成页面的加载
    while 'disabled' not in loading_elem.get_attribute('class'):
        # 若图片的数量已达标，停止向下滚动
        if(int(browser.find_element_by_xpath(XPATH_IMG_NUM_EXPRESSION).get_attribute('data-idx')) >= image_count):
            break
        # 向下滚动
        browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        while 'loading' in loading_elem.get_attribute('class'):
            time.sleep(1)
    '''
    将加载完成的网页转换为xml，使用xpath提取其中的数据
    1. 将 id为 mmComponent_images_1的div元素，中最后一个 li元素中的data-idx属性提取  即可获得当前已经加载的图片数量
    '''
    html_content = etree.HTML(browser.page_source)
    result_imge = html_content.xpath('//*[@id="mmComponent_images_1"]//img[@src]')
    print('---------------')
    browser.save_screenshot("baidu.png")
    browser.close()
    # 下载图片
    flag=0
    imageurl_list = []
    for index,elem in enumerate(result_imge):
        # 处理有些img元素中的src为base64 情况
        if not elem.attrib['src'].startswith('http'):
            flag+=1
            continue
        imageurl_list.append(elem.attrib['src'])
    print(len(result_imge))
    print(flag)
    # 下载图片
    print(key_word,'-----------------开始调用下载器')

    thread_handler(imageurl_list,key_word,path_prefix)



if __name__ == '__main__':
    crawl_info = parse_excel('./data.xlsx',sheet_name='test')
    # print('-------------')
    # print(crawl_info[0][1])

    # 创建进程池
    po = multiprocessing.Pool(MAX_PROCESS_NUMBER)
    while(len(crawl_info)!=0):
        po.apply_async(downloader, tuple(crawl_info.pop()))

    print("-----start-----")
    po.close() # 关闭进程池，关闭后po不再接收新的请求
    po.join() # 等待po中所有子进程执行完成，必须放在close语句之后
    print("-----end-----")
