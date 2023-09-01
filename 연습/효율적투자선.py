import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from Investment import Analyzer

mk = Analyzer.MarketDB()
stocks = ['삼성전자', 'SK하이닉스', '현대자동차', 'NAVER']
df = pd.DataFrame()
for s in stocks:
    df[s] = mk.get_daily_price(code=s, start_date='2016-01-04', end_date='2020-01-04')['close']


daily_ret = df.pct_change()             # pct_change : percentage change <- 연속된 요소 간 백분율 변화 계산
annual_ret = daily_ret.mean() * 252         # 미 증시 열리는 일수 : 252
daily_cov = daily_ret.cov()
annual_cov = daily_cov * 252

port_ret = []
port_risk = []
port_weight = []

print(daily_ret)