from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import pandas as pd
from matplotlib import pyplot as plt

url = 'https://finance.naver.com/item/sise_day.nhn?code=068270&page=1'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
# '''
# html.parser : 속도 적절, 유연한 파싱 가능. lxml보다 느림, html5lib 파서만큼 유연 X
# lxml : 속도 매우 빠름, 유연한 파싱 가능.
# lxml-xml, xml : 속도 매우 빠름, 유연한 파싱 가능. XML 파일만 가능
# html5lib : 웹브라우저와 같은 방식으로 파싱. 극도로 유연, 복잡한 파일 용. 매우 느림
# '''
req = Request(url, headers=headers)
with urlopen(req) as doc:
    html = BeautifulSoup(doc, 'lxml')
    pgrr = html.find('td', class_='pgRR')   # 맨 뒤 찾기
    s = str(pgrr.a['href']).split('=')
    last_page = s[-1]

df = pd.DataFrame()
sise_url = 'https://finance.naver.com/item/sise_day.nhn?code=068270'
for page in range(1, int(last_page) + 1):
    page_url = '{}&page={}'.format(sise_url, page)
    req = Request(page_url, headers=headers)
    
    with urlopen(req) as doc:
        text = BeautifulSoup(doc, 'lxml').prettify()
        tables = pd.read_html(text)
        page_df = tables[0]
        df = pd.concat([df, page_df], ignore_index=True)

df = df.dropna()
print(df)
# df = df.iloc[0:30]
# df = df.sort_values(by='날짜')

# plt.title('Celltrion (close)')
# plt.xticks(rotation=45)
# plt.plot(df['날짜'], df['종가'], 'co-')
# plt.grid(color='gray', linestyle='--')
# plt.show()