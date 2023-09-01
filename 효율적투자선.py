import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from Investment import Analyzer

mk = Analyzer.MarketDB()
stocks = ['삼성전자', 'SK하이닉스', '현대자동차', 'NAVER']
df = pd.DataFrame()
for s in stocks:
    df[s] = mk.get_daily_price(code=s, start_date='2016-01-04', end_date='2020-01-04')['close']

print(df)