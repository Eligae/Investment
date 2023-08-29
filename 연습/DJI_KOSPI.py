import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

dow = pdr.get_data_yahoo('^DJI', '2000-01-04')
kospi = pdr.get_data_yahoo('^KS11', '2000-01-04')

df = pd.DataFrame({'DOW': dow['Close'], 'KOSPI': kospi['Close']})
df = df.fillna(method='bfill')
df = df.fillna(method='ffill')

# import matplotlib.pyplot as plt
# plt.figure(figsize=(7,7))
# plt.scatter(df['DOW'], df['KOSPI'], marker='.')
# plt.xlabel('Dow Jones INdustrail Average')
# plt.ylabel('KOSPI')
# plt.show()
'''
graph의 형식이 y = x 에 가까울수록 직접적인 관계 있음 -> but, 그정도까지는 아닌듯.
미국 증권 시장 & 우리나라 증권 시장
'''

# 선형 회귀식 구하기
# from scipy import stats
# regr = stats.linregress(df['DOW'], df['KOSPI'])
# print(regr)

print(df.corr())
