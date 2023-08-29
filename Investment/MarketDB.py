import pymysql
from datetime import datetime, timedelta
import pandas as pd
import re

import var



class MarketDB:
    def __init__(self):
        """생성자: MariaDB 연결 및 종목코드 Dictionary 생성"""
        self.conn = pymysql.connect(host='localhost', user='root', password=var.PASSWORD, db='Investment_', charset='utf8')
        self.codes = {}
        self.get_comp_info()

    def __del__(self):
        """소멸자 : MariaDB 연결 해제"""
        self.conn.close()

    def get_comp_info(self):
        """company_info table에서 읽어와서 codes에 저장"""
        sql = "SELECT * FROM company_info"
        krx = pd.read_sql(sql, self.conn)
        
        for idx in range(len(krx)):
            self.codes[krx['code'].values[idx]] = krx['company'].values[idx]
    
    def get_daily_price(self, code, start_date=None, end_date=None):
        """KRX 종목의 일별 시세를 DataFrame으로 return
            - code : KRX 종목코드('005930') or 상장기업명('삼성전자')
            - start_date : 조회 시작일('2020-01-01'), 미입력 시 현재의 1년전으로 설정
            - end_date : 조회 종료일('2020-12-31'), 미입력 시 오늘로 설정
        """
        if start_date is None:
            one_year_ago = datetime.today() - timedelta(days=365)
            start_date = one_year_ago.strftime('%Y-%m-%d')
            print(f"start_date is initialized to '{start_date}'")
        else:
            start_lst = re.split('\D+', start_date)
            ## start here

        sql = f"SELECT * FROM daily_price WHERE code = '{code}' and date >= '{start_date}' and date <= '{end_date}'"
        df = pd.read_sql(sql, self.conn)
        df.index = df['date']
        return df
    




    
    