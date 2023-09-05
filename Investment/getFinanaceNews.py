from bs4 import BeautifulSoup
import requests, json, pymysql
import pandas as pd
from datetime import datetime, timedelta
import var

class getNews:
    def __init__(self):
        """생성자 : 기본 url 주소를 받아옴"""
        self.url = var.NEWS_URL
        self.conn = pymysql.connect(host='localhost', user='root', password=var.PASSWORD, db='Investment_', charset='utf8')
        
        # with self.conn.cursor() as curs:
        #     sql = """
        #     CREATE TABLE IF NOT EXISTS news_title (
        #         code
        #     )
        #     """

    def __del__(self):
        """소멸자 : pass"""
        pass
    
    def getNewsByDate(self, date=None):
        """
        - date : format as '20230901'. then, url = url + '&date={date}'
        날짜를 받아와서 해당 날에 대한 finance.naver의 주소 구하고, 크롤링 실행
        return DataFrame
        """
        if date == None:
            date = self.getFormattedDate(date=date)

        today = datetime.today().strftime('%Y%m%d')
        links_ = []
        titles_ = []
        date_ = []
        newspaper_ = []
        
        while today >= date:
            try:
                html = BeautifulSoup(requests.get(url=f"{var.NEWS_URL}&date={date}", headers=var.HEADERS).text, 'lxml')
                pgrr = html.find('td', class_='pgRR')
                if pgrr is None:
                    return None
                s = str(pgrr.a['href']).split('=')
                lastpage = int(s[-1])

                for page in range(1, lastpage+1):
                    pg_url = f'{var.NEWS_URL}&date={date}&page={page}'
                    html = BeautifulSoup(requests.get(url=pg_url, headers=var.HEADERS).text,'lxml', from_encoding='utf-8')
                    # news link, title
                    news_dd = html.find_all('dd', class_='articleSubject')
                    news_dt = html.find_all('dt', class_='articleSubject')
                    # news summary, newspaper company name
                    news_summary = html.find_all('dd', class_='articleSummary')
                    print(f'[{date}] {page}/{lastpage} downloading..')

                    for tag in news_dd+news_dt:
                        a_tag = tag.find('a')
                        links_.append(a_tag['href'])
                        titles_.append(a_tag['title'])
                        date_.append(date)
                    
                    for newspaper in news_summary:
                        span_class = newspaper.find('span')
                        newspaper_.append(span_class.text)
                date = (datetime.strptime(date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
            
            # for Exceptions, make json file to know where the problem has occured
            except Exception as e:
                print('Exception occured :', str(e))

                exception_data = {
                    'date': date,
                    'error_code':e
                }

                try:
                    with open('exception_news.json', 'r') as json_file:
                        existing_data = json.load(json_file)
                        existing_data['data'].append(exception_data)
                except FileNotFoundError:
                    existing_data = {'data': [exception_data]}
                    with open('exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

        # with list of data, create Dataframe in order to save into Maria DB
        NewsDF = pd.DataFrame({'link' : links_, 'title' : titles_, 'date' : date_, 'newspaper' : newspaper_})
        return NewsDF
    
    def getridOfTitles(self, df):
        """
        From 

        ```python 
        def getNewsByDate
        ```
        get ```NewsDF```, 필요없는 내용 삭제하는 함수
        """


    def getFormattedDate(self, date=None):
        """
        - date : format 안된 date를 getNewsByDate에서 실행할 수 있게 적절히 변환.

        None일 경우, 오늘의 날짜로 변경

        return date(string)
        """
        if date == None:
            today = (datetime.today()).strftime('%Y%m%d')
            return today

        return date   
    
    def activate(self, date=0):
        """
        - 실제로 실행할 기간 정함. default = 0 이면 현재 날만 실행
        - 만약 특정 날 입력 시, 그 날부터 현재까지 getNewsByDate 실행함.
        """
        
if __name__ == "__main__":
    getNewsActivate = getNews()
    getNewsActivate.getNewsByDate(date='20230831')