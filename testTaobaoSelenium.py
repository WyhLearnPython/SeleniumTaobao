# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from lxml import etree
from config import *
from urllib.parse import quote

import pymongo


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)

wait = WebDriverWait(browser, 10)
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def index_page(page):
    '''
    抓取索引页
    :param page: 页码
    '''
    print('正在爬取第', page, '页')
    try:
        url = 'https://s.taobao.com/search?q=' + quote(KEYWORD)
        browser.get(url)
        if page > 1:
            input = wait.until(
                EC.presence_of_element_located((By.XPATH, '//input[@aria-label="页码输入框"]'))
            )
            submit = wait.until(
                EC.presence_of_element_located((By.XPATH, '//span[@class="btn J_Submit"]'))
        )
            input.clear()
            input.send_keys(page)
            submit.click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@class="num" and text()={}]'.format(page)))
        )
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-category="auctions"]'))
)
        get_products()
    except TimeoutException:
        index_page(page)

def get_products():
    '''
    提取商品数据
    '''
    html = browser.page_source
    doc = etree.HTML(html)
    items = doc.xpath('//div[@id="mainsrp-itemlist"]//div[@class="items"]//div[@data-index]')
    print(len(items))
    f = lambda x: x[0] if x else None
    for item in items:
        product = {
            'image': f(item.xpath('.//img/@src')),
            'price': f(item.xpath('.//strong/text()')),
            'deal': f(item.xpath('.//div[@class="deal-cnt"]/text()')),
            'title': ''.join(item.xpath('.//a[@class="J_ClickStat"]/text()')).strip(),
            'shop': ''.join(item.xpath('.//div[@class="shop"]/a//text()')).strip(),
            'location': f(item.xpath('.//div[@class="location"]/text()')),
            'link': f(item.xpath('.//a[@class="J_ClickStat"]/@href'))
        }
        print(product)
        save_to_mongo(product)


def save_to_mongo(product):
    '''
    存储到MongoDB
    :param product: 查询到的数据，字典形式
    '''
    try:
        if db[MONGO_COLLECTION].update({'link': product['link']}, {'$set': product}, True):
            print('存储到MongoDB成功!')
    except Exception:
        print('存储到MongoDB失败！')


def main():
    '''
    遍历每一页
    '''
    for i in range(1, MAX_PAGE+1):
        index_page(i)
    browser.close()

if __name__ == '__main__':
    main()

