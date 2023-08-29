import pandas as pd
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from mplfinance.original_flavor import candlestick_ohlc     # OHLC : Open - High - Low - Close(시가 - 고가 - 저가 - 종가)
from datetime import datetime

url = 'https://finance.naver.com/item/sise_day.nhn?code=068270&page=1'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
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
df = df.iloc[0:30]
df = df.sort_values(by='날짜')
for idx in range(0, len(df)):
    dt = datetime.strptime(df['날짜'].values[idx], '%Y.%m.%d').date()
    df['날짜'].values[idx] = mdates.date2num(dt)
ohlc = df[['날짜', '시가', '고가', '저가', '종가']]

plt.figure(figsize=(9,6))
ax = plt.subplot(1,1,1)
plt.title('Celltrion (mpl_finance candle stick)')
candlestick_ohlc(ax, ohlc.values, width=0.7, colorup='red', colordown='blue')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
plt.grid(color='gray', linestyle='--')
plt.show()