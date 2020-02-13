from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


browser = webdriver.Chrome()
url='https://cn.bing.com/images/trending?FORM=BESBTB&ensearch=1'
browser.get(url)
browser.find_element_by_id("sb_form_q").send_keys(u"烤鸭")
browser.find_element_by_id("sb_go_par").click()
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="su"]'))
    )
    text = driver.page_source
    print("text", text)
finally:
    browser.quit()

element = browser.find_elements_by_tag_name("img")
print(element)
browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
time.sleep(6)
browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
time.sleep(6)
browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
time.sleep(6)
browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
time.sleep(6)
browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
browser.save_screenshot("baidu.png")

# print(browser.page_source)
browser.close()