# thu-library

这是一个简单的python爬虫程序，用以检索清华大学图书馆中指定ISBN图书的馆藏信息，可以返回馆藏是否有该图书，若还在订购中则返回“订购中”，若该书目前在库，则直接返回索书号

## 输入

请将待查询数目的ISBN号放入”查询.txt“，规则：每行一个索书号且不需要分隔符，如：

```
9780198832638
9781138484337
9783161555886
9781138478251
```

同时我也放置了一些测试数据供大家参考，见“查询.txt”

## 使用

使用非常简单，直接调用python脚本即可，程序运行过程中会显示当前查询书目的状态，便于大家监控查询进度，如：

```
[2/4]ISBN:9783518283233,订购中
```

## 输出

结果会直接返回每条数目的状态信息，与输入内容逐行对应，其中数目的状态信息有：

N：表示未检索到书目信息，如：ISBN 9783518283233

订购中：表示水木搜索中可以检索到该条信息，但是该图书正在订购中，还未入库，如：ISBN 9783518283233

索书号：如该图书已经在架上则直接返回索书号，如：ISBN 9780198833567 则返回 `B087 FA97`

Tips：该程序只会输出显示为”图书“的条目，”评论“等与本书无关的条目并不会被显示

