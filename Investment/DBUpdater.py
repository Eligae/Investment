import pymysql
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import json, calendar
from threading import Timer

import var

class DBUpdater:
    def __init__(self):
        """생성자 : Maria DB 연결 및 종목코드 Dictionary 생성"""
        self.conn = pymysql.connect(host='localhost', user='root', password=var.PASSWORD, db='Investment_', charset='utf8')
        
        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info (
                code VARCHAR(20),
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY (code))          
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price (
                code VARCHAR(20),
                date DATE,
                open BIGINT(20),
                high BIGINT(20),
                low BIGINT(20),
                close BIGINT(20),
                diff BIGINT(20),
                volume BIGINT(20),
                PRIMARY KEY (code, date))
            """
            curs.execute(sql)
        self.conn.commit()
        self.codes = dict()
        self.update_comp_info()

    def __del__(self):
        """소멸자 : Maria DB 연결 해제"""

    def read_krx_code(self):
        """KRX로 부터 상장법인목록 파일을 읽어와서 데이터프레임으로 변환"""
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        krx = pd.read_html(url, header=0)[0]
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드' : 'code', '회사명' : 'company'})
        krx.code = krx.code.map('{:06d}'.format)
        return krx

    def update_comp_info(self):
        """종목코드를 company_info table에 Update, Dictionary에 저장"""
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
        
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]] = df['company'].values[idx]
        
        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')

            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                krx = self.read_krx_code()
                
                for idx in range(len(krx)):
                    code = krx.code.values[idx]
                    company = krx.company.values[idx]
                    sql = f"REPLACE INTO company_info (code, company, last_update) VALUES ('{code}', '{company}', '{today}')"
                    curs.execute(sql)

                    self.codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] {idx:04d} REPLACE INTO company_info VALUES ({code}, {company}, {today})")
                self.conn.commit()
                print("'")
            else:
                print("Don`t need to get more data - update_comp_info")

    def read_naver(self, code, company, pages_to_fetch):
        """finance/naver.com에서 주식 시세를 읽어 DataFrame으로 반환"""
        try:
            url = f"http://finance.naver.com/item/sise_day.nhn?code={code}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            req = Request(url, headers=headers)
            with urlopen(req) as doc:
                html = BeautifulSoup(doc, 'lxml')
                pgrr = html.find('td', class_='pgRR')
                s = str(pgrr.a['href']).split('=')
                last_page = s[-1]
            df = pd.DataFrame()
            pages = min(int(last_page), pages_to_fetch)

            print(last_page, pages_to_fetch)

            for page in range(1, pages + 1):
                page_url = '{}&page={}'.format(url, page)
                req = Request(page_url, headers=headers)

                with urlopen(req) as doc:
                    text = BeautifulSoup(doc, 'lxml').prettify()
                    tables = pd.read_html(text)
                    page_df = tables[0]
                    df = pd.concat([df, page_df], ignore_index=True)
                
                tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                print('[{}] {} ({}) : {:04d}/{:04d} pages are downloading..'.format(tmnow, company, code, page, pages), end='\r')
            
            df = df.rename(columns={'날짜':'date', '종가':'close', '전일비':'diff', '시가':'open', '고가':'high', '저가':'low', '거래량':'volume'})
            df['date'] = df['date'].replace('.', '-')
            df=df.dropna()

            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df['close', 'diff', 'open', 'high', 'low', 'volume'].astype(int)
            df = df[['date', 'open', 'high', 'low', 'volume']]

        except Exception as e:
            print(f'Exception occured : {e} \nat {company}')
            return None
        return df

    def replace_into_db(self, df, num, code, company):
        """finance/naver.com에서 받아온 주식 시세를 DB에 Update"""
        with self.conn.cursor() as curs:
            for r in df.itertuples():
                sql = f"REPLACE INTO daily_price VALUES ('{code}', {r.date}, {r.open}, {r.high}, {r.low}, {r.close}, {r.diff}, {r.volume})"
                curs.execute(sql)
            self.conn.commit()

            print('[{}] ${:04d} {} ({}) : {} rows > REPLACE INTO daily_price [OK]'.format(datetime.now().strftime('%Y-%m-%d %H:%M'), num+1, company, code, len(df)))

    def update_daily_price(self, pages_to_fetch):
        """KRX 상장법인의 주식 시세를 finance/naver.com에서 읽어서 DB에 Update"""
        for idx, code in enumerate(self.codes):
            df = self.read_naver(code, self.codes[code], pages_to_fetch)
            if df is None:
                continue
            self.replace_into_db(df, idx, code, self.codes[code])

    def execute_daily(self):
        """실행 즉시, 매일 17:00에 daily_price table Update"""
        self.update_comp_info()
        try:
            with open('./config.json', 'r') as in_file:
                config = json.load(in_file)
                pages_to_fetch = config['pages_to_fetch']

        except FileExistsError:
            with open('./config.json', 'w') as out_file:
                pages_to_fetch = 100
                config = {'pages_to_fetch' : 1}
                json.dump(config, out_file)

        self.update_daily_price(pages_to_fetch)

        tmnow = datetime.now()
        lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
        if tmnow.month == 12 and tmnow.day == lastday:
            tmnext = tmnow.replace(year=tmnow.year+1, month=1, day=1, hour=17, minute=0, second=0)
        elif tmnow.day == lastday:
            tmnext = tmnow.replace(month=tmnow.month+1, day=1, hour=17, minute=0, second=0)
        else:
            tmnext = tmnow.replace(day=tmnow.day+1, hour=17, minute=0, second=0)
        tmdiff = tmnext-tmnow
        secs = tmdiff.seconds

        t = Timer(secs, self.execute_daily)
        print("Waiting for next update ({})".format(tmnext.strftime('%Y-%m-%d %H:%M')))
        t.start()

if __name__ == '__main__':
    dbu = DBUpdater()
    dbu.execute_daily()