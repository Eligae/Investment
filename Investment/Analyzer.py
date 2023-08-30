import pandas as pd
import pymysql
from datetime import datetime, timedelta
import re
import var

class MarketDB:
    def __init__(self):
        """생성자 : MariaDB 연결 및 종목코드 Dictionary 생성"""
        self.conn = pymysql.connect(host='localhost', user='root', password=var.PASSWORD, db='Investment_', charset='utf8')
        self.codes = {}
        self.get_comp_info()
    
    def __del__(self):
        """소멸자 : MariaDB 연결 해제"""
        sql = "SELECT * FROM company_info"
        krx = pd.read_sql(sql, self.conn)
        
        for idx in range(len(krx)):
            self.codes[krx['code'].values[idx]] = krx['company'].values[idx]
    
    def get_daily_price(self, code, start_date=None, end_date=None):
        """
        KRX 종목의 일별 시세를 Dataframe 형식으로 반환
        - code : KRX 종목코드 or 상장기업명
        - start_date : 조회시작일, default : today - 1year
        - end_date : 조회종료일, default : today
        """
        if (start_date is None):
            one_year_ago = datetime.today() - timedelta(days=365)
            start_date = one_year_ago.strftime('%Y-%m-%d')
            print(f"start_date is initialized to '{start_date}'")
        else:
            start_date = self.getFormattedDate('start', start_date)
        
        if (end_date is None):
            end_date = datetime.today().strftime('%Y-%m-%d')
            print(f"end_date is initialized to '{end_date}'")      
        else:
            end_date = self.getFormattedDate('end', end_date)

        codes_keys = list(self.codes.keys())
        codes_values = list(self.codes.values())
        
        if code in codes_keys:
            pass
        elif code in codes_values:
            idx = codes_values.index(code)
            code = codes_keys[idx]
        else:
            print(f"ValueError : Code({code}) doesn`t exist")
        
        sql = f"SELECT * FROM daily_price WHERE code = '{code}' and date >= '{start_date}', date <= '{end_date}'"
        df = pd.read_sql(sql, self.conn)
        df.index = df['date']
        return df

    def getFormattedDate(self, when, date):
        """
        날짜를 받아서 맞는 형식으로 바꾸어주는 함수
        - when : terminal에서 언제의 값을 설정하는 것인지 확인용('start', 'end')
        - date : 입력받은 날짜 -> 정규표현식을 사용해 맞는 형식으로 변경

        return : 올바른 형식의 날짜(string)
        """
        re_lst = re.split('\D+', date)
        if (re_lst[0] == ''):
            re_lst = re_lst[1:]
        
        re_year = int(re_lst[0])
        re_month = int(re_lst[1])
        re_day = int(re_lst[2])

        if re_year < 1900 or re_year > 2200:
            print(f"ValueError! : {when}_year({re_year}) is wrong!")
            return
        if re_month < 1 or re_month > 12:
            print(f"ValueError! : {when}_month({re_month}) is wrong!")
            return
        if re_day < 1 or re_day > 31:
            print(f"ValueError! : {when}_day({re_day}) is wrong")
            return
        
        re_date = f"{re_year:04d}-{re_month:02d}-{re_day:02d}"
        return re_date