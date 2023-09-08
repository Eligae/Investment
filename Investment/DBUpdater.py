import pandas as pd
from bs4 import BeautifulSoup
import pymysql, calendar, json
import requests
from datetime import datetime
from threading import Timer
import xml.etree.ElementTree as ET
import zipfile
import io
from pandas import json_normalize

import var

class DBUpdater:  
    def __init__(self):
        """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
        self.conn = pymysql.connect(host='localhost', user='root', password=var.PASSWORD, db='Investment_', charset='utf8')
        
        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info (
                stock_code VARCHAR(20),
                corp_code VARCHAR(20), 
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY (code))
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price (
                stock_code VARCHAR(20),
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
               
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.conn.close() 
     
    def read_krx_code(self):
        """KRX로부터 상장기업 목록 파일을 읽어와서 데이터프레임으로 반환"""
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        krx = pd.read_html(url, header=0)[0]
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.map('{:06d}'.format)
        return krx
    
    def read_dart_code(self, api_key):
        """DART에서 API를 이용해 xml파일을 읽어온 후 상장기업 목록 데이터 프레임으로 반환"""

        url = 'https://opendart.fss.or.kr/api/corpCode.xml'
        params = {'crtfc_key': api_key,}

        r = requests.get(url, params = params)
        try:
            tree = ET.XML(r.content)
            status = tree.find('status').text
            message = tree.find('message').text
            if status != '000':
                raise ValueError({'status': status, 'messgae': message})
        except ET.ParseError as e:
            pass

        zf = zipfile.ZipFile(io.BytesIO(r.content))
        xml_data = zf.read('CORPCODE.xml')

        tree = ET.XML(xml_data)
        all_records = []

        element = tree.findall('list')
        for i, child in enumerate(element):
            record = {}
            for i, subchild in enumerate(child):
                record[subchild.tag] = subchild.text
            all_records.append(record)

        corp_code = pd.DataFrame(all_records)

        return corp_code
    

    def compare_krx_dart_df(self, krx, dart):
        """dart stock code - krx stock code, 상장된 기업 중 재무재표만 있는 stock code만 남겨 데이터프레임으로 반환"""
        dart['stock_code'] = dart['stock_code'].replace(' ', pd.NA)
        dart = dart.dropna()

        filtered_stock_code = pd.concat([krx['code'], dart['stock_code']]).drop_duplicates()

        filtered_dart = dart[dart['stock_code'].str.contains('|'.join(filtered_stock_code))]
        filtered_krx = krx[krx['code'].str.contains('|'.join(filtered_stock_code))]

        merge_df = pd.merge(filtered_dart, filtered_krx, left_on = 'stock_code', right_on = 'code', how = 'inner')

        return merge_df
    
    def update_comp_info(self):
        """종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장"""

        api_key = 'ede53418cf88e7dd3088078b7406d3faeeeba07b'

        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
       
        for idx in range(len(df)):
            self.codes[df['stock_code'].values[idx]] = df['company'].values[idx]
                    
        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')
            
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
    
                dart_df = self.read_dart_code(api_key)
                krx_df = self.read_krx_code()

                merge_df = self.compare_krx_dart_df(krx_df, dart_df)
                
            
                for idx in range(len(merge_df)):
                    stock_code = merge_df.stock_code.values[idx]
                    corp_code = merge_df.corp_code.values[idx]
                    company = merge_df.company.values[idx]                
                    sql = f"REPLACE INTO company_info (stock_code, corp_code, company, last_update) VALUES ('{stock_code}','{corp_code}', '{company}', '{today}')"
                    curs.execute(sql)
            
                    self.codes[stock_code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info VALUES ({stock_code}, {corp_code}, {company}, {today})")
                self.conn.commit()
                print('')              

    def read_naver(self, stock_code, company, pages_to_fetch, skip=0):
        """네이버에서 주식 시세를 읽어서 데이터프레임으로 반환
            - stock_code        : 회사 번호 -> finance.naver.com에서 쓰일 값
            - company           : 회사 이름 -> terminal에서 표기용
            - pages_to_fetch    : 총 몇 page를 crawling 할 것인가?
            - skip              : 처음 다운받을 경우, 다시 다운받을 때 회사코드값 넣으면 그 전까지 skip함.
        """
        tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 중간에 다운받다가 끊을 경우, read_naver함수의 skip값에 끊기 직전의 회사 코드번호 입력시 전의 data 모두 skip.
        if int(stock_code) < skip:    
            print('[{}] {} ({}) :  is skipped..'.
                    format(tmnow, company, stock_code), end="\n")
            return None
        
        try:
            # 23.09.04 기준 '일별시세' 탭 없어짐. 18
            url = f"https://finance.naver.com/item/sise_day.nhn?code={stock_code}&page=1"
            html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, "lxml")
            pgrr = html.find("td", class_="pgRR")
            print(pgrr)
            if pgrr is None:
                return None
                
            s = str(pgrr.a["href"]).split('=')
            lastpage = s[-1] 
            df = pd.DataFrame()
            pages = min(int(lastpage), pages_to_fetch)                  
            # 처음 실행시에만 max로 설정. 이후는 min으로 설정해도 무리 없음.
            # [주의] : 처음 Database 다운받을 경우. 정말 오래걸리니 잘때 하는 것을 추천함.
            for page in range(1, pages + 1):
                pg_url = '{}&page={}'.format(url, page)

                new_data = pd.read_html(requests.get(pg_url,
                    headers={'User-agent': 'Mozilla/5.0'}).text)[0]
                df = pd.concat([df, new_data], ignore_index=True)
            
                
                print('[{}] {} ({}) : {:04d}/{:04d} pages are downloading...'.
                    format(tmnow, company, stock_code, page, pages), end="\r")
                
            df = df.rename(columns={'날짜':'date', '종가':'close', '전일비':'diff', '시가':'open', '고가':'high', '저가':'low', '거래량':'volume'})
            df['date'] = df['date'].replace('.', '-')
            df = df.dropna()
            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df[['close','diff', 'open', 'high', 'low', 'volume']].astype(int)
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        
        except Exception as e:
            print('Exception occured :', str(e))

            exception_data = {
                'stock_code': stock_code,
                'company': company,
                'pages_to_fetch': pages_to_fetch
            }

            try:
                with open('json\\exception_data.json', 'r') as json_file:
                    existing_data = json.load(json_file)
                    existing_data['data'].append(exception_data)
            except FileNotFoundError:
                existing_data = {'data': [exception_data]}
            
                with open('json\\exception_data.json', 'w') as json_file:
                    json.dump(existing_data, json_file)
                return None
        
        return df
    
    def naver_error_reDownload(self):
        """
        read_naver에서 오류난 부분을 'exception_data.json'에 저장하는데, 
        
        그 부분에 해당하는 것만 다시 실행하는 과정.
        
        실행 모두 완료되면, 그에 따라서 exception_data.json에서 값 삭제함.
        """

        # with open('json\\exception_data.json', 'r') as exceptionData:
            


    def replace_into_db(self, df, num, stock_code, company):
        """네이버에서 읽어온 주식 시세를 DB에 REPLACE"""
        with self.conn.cursor() as curs:
            for r in df.itertuples():
                sql = f"REPLACE INTO daily_price VALUES ('{stock_code}', "\
                    f"'{r.date}', {r.open}, {r.high}, {r.low}, {r.close}, "\
                    f"{r.diff}, {r.volume})"
                curs.execute(sql)
            self.conn.commit()
            
            print('[{}] # {:04d} - {} ({}) : {} rows > REPLACE INTO daily_price [OK]'.format(datetime.now().strftime('%Y-%m-%d %H:%M'), num+1, company, code, len(df)))

    def update_daily_price(self, pages_to_fetch):
        """KRX 상장법인의 주식 시세를 네이버로부터 읽어서 DB에 업데이트"""  
        for idx, stock_code in enumerate(self.codes):
            df = self.read_naver(code=stock_code, company=self.codes[stock_code], pages_to_fetch=pages_to_fetch)
            
            if df is None:
                continue
            
            self.replace_into_db(df, idx, stock_code, self.codes[stock_code])     

    # def getCompanyItem(self, code)       
    #     url = f'https://finance.naver.com/item/main.naver?code={code}'
    #     tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')

    #     try:
    #         html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, "lxml")
    #         item = html.find("")



    def execute_daily(self):
        """실행 즉시 및 매일 오후 다섯시에 daily_price 테이블 업데이트"""
        self.update_comp_info()
        
        try:
            with open('json\\config.json', 'r') as in_file:
                config = json.load(in_file)
                pages_to_fetch = config['pages_to_fetch']
        
        except FileNotFoundError:
            with open('json\\config.json', 'w') as out_file:
                pages_to_fetch = 100 
                config = {'pages_to_fetch': 1}
                json.dump(config, out_file)
        
        print("Ready to get daily price from finance.naver.com...")
        self.update_daily_price(pages_to_fetch)

        tmnow = datetime.now()
        lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
        
        if tmnow.month == 12 and tmnow.day == lastday:
            tmnext = tmnow.replace(year=tmnow.year+1, month=1, day=1,
                hour=17, minute=0, second=0)
        
        elif tmnow.day == lastday:
            tmnext = tmnow.replace(month=tmnow.month+1, day=1, hour=17,
                minute=0, second=0)
        
        else:
            tmnext = tmnow.replace(day=tmnow.day+1, hour=17, minute=0,
                second=0)   
        
        tmdiff = tmnext - tmnow
        secs = tmdiff.seconds
        t = Timer(secs, self.execute_daily)
        
        print("Waiting for next update ({}) ... ".format(tmnext.strftime('%Y-%m-%d %H:%M')))
        t.start()

if __name__ == '__main__':

    dbu = DBUpdater()
    dbu.execute_daily()
