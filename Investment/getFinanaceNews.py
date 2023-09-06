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
        db_url = f'mysql+pymysql://root:{var.PASSWORD}@localhost/Investment_?charset=utf8'
        self.engine = create_engine(db_url) 

    def __del__(self):
        """소멸자 : pass"""
        self.engine.dispose()
    
    def createNewsTable(self):
        """
        - ```news table``` 이 Maria DB에 없는 경우, 생성함
        """
            
    def storeNewsDataInDataBase(self, NewsDF):
        """
        News data를 MariaDB database에 저장
        """


    def getNewsByDate(self, date=None, end_date=None) -> pd.DataFrame: 
        """
        - date : format as '20230901'. then, url = url + '&date={date}'

        날짜를 받아와서 해당 날에 대한 finance.naver의 주소 구하고, 크롤링 실행
        """
        if date == None:            # 초기 날짜 설정, 입력 없으면 현재 날짜로..
            date = self.getFormattedDate(date=date)
        if end_date == None:        # 끝나는 날짜 설정, 입력 없으면 현재 날짜로..
            end_date = datetime.today().strftime('%Y%m%d')

        NewsDF = pd.DataFrame(columns=['article_id', 'office_id', 'title', 'date', 'page', 'newspaper'])    # 기본적인 빈 Dataframe 생성 
        
        while end_date >= date:     # 날짜별 크롤링. 끝나는 날짜까지 실행
            titles_day = [] # 제목
            date_day = []   # 날짜
            newspaper_day = []  # 신문사 이름
            article_id_day = [] # 기사 고유 코드
            office_id_day = []  # 신문사 이름명
            page_day = []   # url상의 기사 page 값
            # 위의 list 중, article_id, office_id, page를 합치면 기사 link가 됨.

            try:        # Crawling 중, 오류가 나올 수 있으므로, 예외처리를 함

                # 뉴스 링크(finance naver 실시간 속보) 해당 날짜에 따라 찾기
                html = BeautifulSoup(requests.get(url=f"{var.NEWS_URL}&date={date}", headers=var.HEADERS).text, 'lxml')    
                pgrr = html.find('td', class_='pgRR')   # 맨 마지막 페이지 찾기
                if pgrr is None:        # 마지막 페이지 없으면 실패 <- 페이지가 오류난 경우
                    return None
                
                s = str(pgrr.a['href']).split('=')
                lastpage = int(s[-1])   # 페이지 값 int형식으로 가져옴

                for page in range(1, lastpage+1):       # 뉴스 링크의 페이지 별로 실행
                    pg_url = f'{var.NEWS_URL}&date={date}&page={page}'      # 링크 페이지에 맞게 추가
                    html = BeautifulSoup(requests.get(url=pg_url, headers=var.HEADERS).text,'lxml') # html 형식으로 가져옴
                    # 뉴스 링크, 제목 가져옴
                    # 뉴스 링크, 제목을 포함하는 dd, dt 총 2개로 나누어져 있음. 둘다 가져오기
                    news_dd = html.find_all('dd', class_='articleSubject')
                    news_dt = html.find_all('dt', class_='articleSubject')
                    # news summary, newspaper company name은 dd로만 있음
                    news_summary = html.find_all('dd', class_='articleSummary')
                    print(f'[{date}] {int(page):02d}/{int(lastpage):02d} downloading...', end='\r')     # 다운로드 표시창.

                    for tag in news_dd + news_dt:     # 뉴스 링크, 제목의 html 구조에서 제목, 날짜, 링크 떼오기
                        """
                        news_dd + new_dt의 배열 요소 예시
                        <dd class="articleSubject">
							<a href="/news/news_read.naver?article_id=0001123637&office_id=215&mode=LSS2D&type=0&section_id=101&section_id2=258&section_id3=&date=20230906&page=1" title="EU, 빅테크 특별규제 '애플&middot;구글 등 6개사' 확정">EU, 빅테크 특별규제 '애플&middot;구글 등 6개사' 확정</a>
						</dd>
                        """
                        a_tag = tag.find('a')
                        titles_day.append(a_tag['title'])
                        date_day.append(date)

                        link = a_tag['href'].split('?')[-1]     # 링크 분해해서 article_id, office_id 가져옴
                        params = link.split('&')
                        for param in params:
                            key, value = param.split('=')
                            if key == 'article_id':
                                article_id_day.append(value)
                            elif key == 'office_id':
                                office_id_day.append(value)
                        page_day.append(page)                   # page 값도 저장

                    for newspaper in news_summary:          # 뉴스 회사명 가져오기
                        span_class = newspaper.find('span')
                        newspaper_day.append(span_class.text)
                    
                    
                    # 이 list들을 합쳐서 하루의 Dataframe을 만듬
                    day_DF = pd.DataFrame({'article_id':article_id_day, 'office_id': office_id_day, 'title': titles_day, 'date': date_day, 'page': page_day, 'newspaper': newspaper_day})
                    # 가끔 중복되는 기사 있어서 제목 같으면 없앴음
                    day_DF = day_DF.drop_duplicates(subset='title', keep='first')
          
            # for Exceptions, make json file to know where the problem has occured
            except Exception as e:
                print('Exception occured :', str(e))
                exception_data = {          # 날짜, 오류의 이유를 json 형식으로 만들어서 저장. 
                    'date': date,           # 나중에 json 확인하고, 그 날짜만 실행하면 다시 정상적으로 저장할 수 있기 때문
                    'error_code':str(e)
                }

                try:
                    with open('exception_news.json', 'r') as json_file: # exception_news.json에 오류 data 저장
                        existing_data = json.load(json_file)
                        existing_data['data'].append(exception_data)
                    
                    with open('exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

                except FileNotFoundError:       # exception_news.json이 없으면 새로 만들어서 저장
                    existing_data = {'data': [exception_data]}
                    with open('exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

            NewsDF = pd.concat([NewsDF, day_DF], ignore_index=True)
            date = (datetime.strptime(date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')       # 다음날로 넘어감

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