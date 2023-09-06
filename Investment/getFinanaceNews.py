from bs4 import BeautifulSoup
import requests, json
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import var

class getNews:
    def __init__(self):
        """생성자 : 기본 url 주소를 받아옴"""
        self.url = var.NEWS_URL
        # db_url = f'mysql+pymysql://root:{var.PASSWORD}@localhost/Investment_?charset=utf8'
        # self.engine = create_engine(db_url) 

    def __del__(self):
        """소멸자 : pass"""
        # self.engine.dispose()
    
    def getNewsByDate(self, date=None, end_date=None) -> pd.DataFrame: 
        """
        - date : format as '20230901'. then, url = url + '&date={date}'

        날짜를 받아와서 해당 날에 대한 finance.naver의 주소 구하고, 크롤링 실행
        """
        if date == None:
            date = self.getFormattedDate(date=date)
        if end_date == None:
            end_date = datetime.today().strftime('%Y%m%d')
        NewsDF = pd.DataFrame(columns=['article_id', 'office_id', 'title', 'date', 'page', 'newspaper'])
        
        while end_date >= date:
            titles_day = []
            date_day = []
            newspaper_day = []
            article_id_day = []
            office_id_day = []
            page_day = []

            try:
                html = BeautifulSoup(requests.get(url=f"{var.NEWS_URL}&date={date}", headers=var.HEADERS).text, 'lxml')
                pgrr = html.find('td', class_='pgRR')
                if pgrr is None:
                    return None
                s = str(pgrr.a['href']).split('=')
                lastpage = int(s[-1])

                for page in range(1, lastpage+1):
                    pg_url = f'{var.NEWS_URL}&date={date}&page={page}'
                    html = BeautifulSoup(requests.get(url=pg_url, headers=var.HEADERS).text,'lxml') #from_encoding='utf-8')
                    # news link, title
                    news_dd = html.find_all('dd', class_='articleSubject')
                    news_dt = html.find_all('dt', class_='articleSubject')
                    # news summary, newspaper company name
                    news_summary = html.find_all('dd', class_='articleSummary')
                    print(f'[{date}] {int(page):02d}/{int(lastpage):02d} downloading...', end='\r')

                    for tag in news_dd+news_dt:
                        a_tag = tag.find('a')
                        titles_day.append(a_tag['title'])
                        date_day.append(date)

                        link = a_tag['href'].split('?')[-1]
                        params = link.split('&')
                        for param in params:
                            key, value = param.split('=')
                            if key == 'article_id':
                                article_id_day.append(value)
                            elif key == 'office_id':
                                office_id_day.append(value)
                        page_day.append(page)

                    for newspaper in news_summary:
                        span_class = newspaper.find('span')
                        newspaper_day.append(span_class.text)
                    
                    
                    
                    day_DF = pd.DataFrame({'article_id':article_id_day, 'office_id': office_id_day, 'title': titles_day, 'date': date_day, 'page': page_day, 'newspaper': newspaper_day})
                    day_DF = day_DF.drop_duplicates(subset='title', keep='first')
          
            # for Exceptions, make json file to know where the problem has occured
            except Exception as e:
                print('Exception occured :', str(e))
                exception_data = {
                    'date': date,
                    'error_code':str(e)
                }

                try:
                    with open('exception_news.json', 'r') as json_file:
                        existing_data = json.load(json_file)
                        existing_data['data'].append(exception_data)
                    
                    with open('exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

                except FileNotFoundError:
                    existing_data = {'data': [exception_data]}
                    with open('exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

            NewsDF = pd.concat([NewsDF, day_DF], ignore_index=True)
            date = (datetime.strptime(date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')

        # to check the structure & values of the DataFrame : NewsDF...
        # NewsDF.to_csv('news_data_re.csv', encoding='utf-8', index=False)
        print()
        return NewsDF
    
    def getridOfTitles(self, df) -> pd.DataFrame:
        """
        From 

        ```python 
        def getNewsByDate
        ```
        get ```NewsDF```, 필요없는 내용 삭제하는 함수
        """


    def getFormattedDate(self, date=None) -> str:
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
    getNewsActivate.getNewsByDate(date=None)