from selenium import webdriver  # 爬虫核心库selenium
from selenium.webdriver.chrome.options import Options  # 导入浏览器内核设置，主要是为了设置无头（headless）模式
from bs4 import BeautifulSoup  # 引入BeautifulSoup库解析html代码
import time


def get(url, ebook=False):  # 通过selenium（webdriver）获取网页全部内容, ebook参数用来区分是否为电子资源
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 设置Chrome为无头模式
    chrome_options.add_argument('no-sandbox')  # 代码不明，主要为了适配centos服务器运行
    chrome_options.add_argument('disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)  # 等待5s使得全部信息加载完成
    if ebook:
        driver.switch_to.frame("iFrameResizer0")   # 若为电子资源需要切换到iframe后再导出源代码
    return BeautifulSoup(driver.page_source, 'html.parser')  # 使用beautifulsoup解析全部网页内容
    driver.close()  # 关闭driver


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
        for i in soup.find_all('div', class_='list-item-wrapper'):
            j = i.find_all('span')
            if j[4].text == '图书' or j[2].text == '图书':  # 首先判断这一条信息是否为“图书”
                if j[-4].text[-4:] == '不可获取':  # 若提示不可获取意味着这本书还在订购，返回订购中的状态
                    return '订购中\n'
                if j[-1].text[-4:] == '在线访问':
                    ebook_url = i.find('a')['href']  # 若为电子资源，需要跳转到新的界面查询其数据库
                    soup = get(ebook_url, ebook=True)
                    return '电子资源：{}'.format(soup.find('a', attrs={'target': '_blank'}).text)

                else:  # 如果不是订购中，也不是电子资源，则直接返回索书号
                    number = soup.find('span', class_='best-location-delivery locations-link').text  # 获取索书号
                    return '{}\n'.format(number)


if __name__ == '__main__':
    # 首先读入数据
    with open('查询.txt', 'r') as f:
        contents = f.readlines()
    ans = []  # 最终生成的结果
    num = 1  # 计数器
    for i in contents:
        result = search(i)  # 调用查询函数，result记录了当前图书查询返回的结果
        print('[{}/{}]ISBN:{},{}'.format(num, len(contents), i.rstrip(), result), end='')  # 输出当前状态，第num条图书，其状态为..
        ans.append(result)
        num += 1
    # 最后输出数据
    with open(r'结果.txt', 'w') as f:  # 输出全部结果到“结果.txt”
        f.writelines(ans)
