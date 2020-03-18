from selenium import webdriver  # 爬虫核心库selenium
from selenium.webdriver.chrome.options import Options  # 导入浏览器内核设置，主要是为了设置无头（headless）模式
from bs4 import BeautifulSoup  # 引入BeautifulSoup库解析html代码
import time


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
            driver.get(url)
            time.sleep(5)
            driver.switch_to.frame("iFrameResizer0")  # 若为电子资源需要切换到iframe后再导出源代码
    soup = BeautifulSoup(driver.page_source, 'html.parser')  # 使用beautifulsoup解析全部网页内容
    driver.close()  # 关闭driver
    return soup


# search 函数，用于搜索指定ISBN是否存在馆藏
def search(isbn):
    # url为查询书目的地址，其中search_scope为检索类型：default_scope为检索全部资源，若检索馆藏纸质资源为thumain_scope
    url = 'https://tsinghua-primo.hosted.exlibrisgroup.com/primo-explore/search?query=any,contains,' \
          '{}&tab=default_tab&search_scope=default_scope&vid=86THU&lang=zh_CN&offset=0 '.format(isbn)
    soup = get(url)

    # 首先判断是否有馆藏
    Exist = True  # Exist变量用于记录是否存在馆藏
    for i in soup.find_all('h2'):
        if i.text == '未找到记录':
            Exist = False  # 若提示未找到记录，则没有检索到资源
    if not Exist:
        return 'N\n'  # 若无馆藏则直接返回N
    else:
        # 已经检索到馆藏信息
        # 首先判断这条信息是不是“图书”，若为“评论”等则为无效信息
        book_ans = ''
        for i in soup.find_all('div', class_='list-item-wrapper'):
            j = i.find_all('span')
            if j[4].text == '图书' or j[2].text == '图书':  # 首先判断这一条信息是否为“图书”
                is_multi = soup.find('span', attrs={'translate': 'nui.frbrversion.found'})  # 增加一个标签判断是否有多个副本信息
                if is_multi:
                    return '存在多个版本，建议根据其他信息手动核查！\n'

                elif j[-4].text[-4:] == '不可获取':  # 若提示不可获取有两种情况：若有索书号则该图书正在借阅中，应返回索书号；否则为这本书正在订购中
                    number = soup.find('span', class_='best-location-delivery locations-link').text  # 获取索书号
                    if not number:  # 若number=None，也就是找不到索书号，则是订购中的状态
                        book_ans += '订购中;'
                    else:
                        book_ans += number + ';'

                elif j[-1].text[-4:] == '在线访问':
                    ebook_url = i.find('a')['href']  # 若为电子资源，需要跳转到新的界面查询其数据库
                    soup = get(ebook_url, ebook=True)
                    book_ans += '电子图书-'
                    for i in soup.find_all('a', attrs={'target': '_blank'}):
                        if i.text != '':
                            book_ans += i.text[:i.text.find(' ')] + ';'  # 近提取电子资源数据库的第一个关键词

                elif j[-1].text[-4:] == '在线全文':
                    book_ans += '在线全文;'
                else:  # 如果不是订购中，也不是电子资源，则直接返回索书号
                    number = soup.find('span', class_='best-location-delivery locations-link')
                    if number:
                        book_ans += number.text + ';'  # 获取索书号

        if book_ans:
            return '{}\n'.format(book_ans[:-1])
        else:
            return 'N\n'  # 若检索到的信息都不是图书则返回N


if __name__ == '__main__':
    # 首先读入数据
    with open('查询.txt', 'r') as f:
        contents = f.readlines()
    ans = []  # 最终生成的结果
    num = 1  # 计数器
    for i in contents:
        for iter_num in range(3):  # 如果遇到没有馆藏，三次查询，防止因为网页未加载完成导致误判断为无馆藏
            result = search(i)  # 调用查询函数，result记录了当前图书查询返回的结果
            if result != 'N\n':
                break
        print('[{}/{}]ISBN:{},{}'.format(num, len(contents), i.rstrip(), result), end='')  # 输出当前状态，第num条图书，其状态为..
        ans.append(result)
        num += 1
    # 最后输出数据
    with open(r'结果.txt', 'w') as f:  # 输出全部结果到“结果.txt”
        f.writelines(ans)
