from selenium import webdriver  # 爬虫核心库selenium
from selenium.webdriver.chrome.options import Options  # 导入浏览器内核设置，主要是为了设置无头（headless）模式
from bs4 import BeautifulSoup  # 引入BeautifulSoup库解析html代码
import time
import sys


def get(url, ebook=False):  # 通过selenium（webdriver）获取网页全部内容, ebook参数用来区分是否为电子资源
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 设置Chrome为无头模式
    chrome_options.add_argument('--no-sandbox')  # 代码不明，主要为了适配centos服务器运行
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)  # 等待5s使得全部信息加载完成
    if ebook:
        try:
            driver.switch_to.frame("iFrameResizer0")  # 若为电子资源需要切换到iframe后再导出源代码
        except:
            pass
    soup = BeautifulSoup(driver.page_source, 'html.parser')  # 使用beautifulsoup解析全部网页内容

    is_multi = soup.find('span', attrs={'translate': 'nui.frbrversion.found'})  # 增加一个标签判断是否有多个副本信息
    if is_multi:  # 判断是否为多条副本信息，若是则需要点击后查看全部的信息
        driver.find_element_by_class_name('prm-notice').click()
        time.sleep(5)  # 等待5s使得全部信息加载完成
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # 使用beautifulsoup解析全部网页内容

    driver.close()  # 关闭driver
    return soup


# search 函数，用于搜索指定ISBN是否存在馆藏
def search(isbn, times=1):  # times 表示第n次查询，若查询结果为N，则至多进行2次查询
    if times > 3:
        return 'N\n'

    # url为查询书目的地址，其中search_scope为检索类型：default_scope为检索全部资源，若检索馆藏纸质资源为thumain_scope
    url = 'https://tsinghua-primo.hosted.exlibrisgroup.com/primo-explore/search?query=any,contains,' \
          '{}&tab=default_tab&search_scope=default_scope&vid=86THU&lang=zh_CN&offset=0 '.format(isbn)
    soup = get(url)

    # 首先判断是否有馆藏，若提示“未找到记录”则直接退出
    for i in soup.find_all('h2'):
        if i.text == '未找到记录':
            return 'N\n'  # 若无藏则直接返回N

    # 已经检索到馆藏信息，开始逐条分析
    ebook_list = []
    book_ans = ''
    for i in soup.find_all('div', class_='list-item-wrapper'):
        j = i.find_all('span')
        # 首先判断这条信息是不是“图书”，若为“评论”等则为无效信息
        if j[4].text == '图书' or j[2].text == '图书':
            # 第一种情况，提示“不可获取”
            if j[-4].text[-4:] == '不可获取':  # 若提示不可获取有两种情况：若有索书号则该图书正在借阅中，应返回索书号；否则为这本书正在订购中
                number = i.find('span', class_='best-location-delivery locations-link')  # 获取索书号
                if not number.text:  # 若找不到索书号，则是订购中的状态
                    book_ans += '订购中;'
                else:
                    book_ans += number.text.rstrip(')').lstrip('(') + ';'  # 获取索书号

            # 第二种情况：在线资源
            elif j[-1].text[-4:] == '在线访问' or j[-1].text[-4:] == '在线全文':
                ebook_url = i.find('a')['href']  # 若为电子资源，需要跳转到新的界面查询其数据库
                soup = get(ebook_url, ebook=True)
                for i2 in soup.find_all('a', attrs={'target': '_blank'}):
                    if i2.text:  # 若内容不为空
                        database_name = i2.text[:i2.text.find(' ')]  # 近提取电子资源数据库的第一个关键词
                        name_dict = {'易阅通电子图': '易阅通', '爱学术电子': '爱学术'}  # 建立一个需要得电子数据库名的字典
                        if database_name in name_dict:
                            database_name = name_dict[database_name]
                        if database_name and database_name not in ebook_list:  # 若数据库名不为空且不在电子数据库列表中
                            ebook_list.append(database_name)

            else:  # 如果不是订购中，也不是电子资源，则为纸质资源，直接返回索书号
                number = i.find('span', class_='best-location-delivery locations-link')
                if number:
                    book_ans += number.text.rstrip(')').lstrip('(') + ';'  # 获取索书号

    # 判断是否存在电子资源
    if ebook_list:
        for i in ebook_list:
            book_ans += '电子图书-' + i + ';'
        book_ans.rstrip(';')

    # 返回查询到的结果
    if book_ans:
        return '{}\n'.format(book_ans[:-1])
    else:
        return search(isbn, times + 1)


if __name__ == '__main__':
    print('欢迎使用清华大学图书馆 馆藏信息查询脚本（作者：Nick WU)')
    print('图书馆官网：http://lib.tsinghua.edu.cn')
    print('-' * 40)

    print('正在读取输入数据...')
    # 首先读入数据
    try:
        with open('查询.txt', 'r') as f:
            contents = f.readlines()
        with open('结果.txt', 'w') as f:  # 新建”结果.txt“用于记录查询后的结果
            pass
    except:
        print('输入数据读取异常或创建输出文件异常')
        sys.exit()
    else:
        print('输入数据读取成功,输出文件已成功建立')

    print('共读取到{}条数据，正在执行查询...'.format(len(contents)))
    time_start = time.time()
    for i in range(len(contents)):
        result = search(contents[i].rstrip('\n'))  # 调用查询函数，result记录了当前图书查询返回的结果
        print('[{}/{}]查询:{} --- 结果:{}'.format(i + 1, len(contents), contents[i].rstrip(), result),
              end='')  # 输出当前状态，第num条图书，其状态为..
        with open('结果.txt', 'a') as f:
            f.write(result)
    print('恭喜您，查询完成！共花费{}s'.format(time.time() - time_start))
