from bs4 import BeautifulSoup
import requests, json, requests
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
        - date : format as ```'20230901'```. then, ```url = url + '&date={date}'```

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
            # 위의 list 중, article_id, office_id, page를 합치면 기사 link가 됨.

            try:        
                html = BeautifulSoup(requests.get(url=f"{var.NEWS_URL}&date={date}", headers=var.HEADERS).text, 'lxml')    
                pgrr = html.find('td', class_='pgRR')   
                if pgrr is None:       
                    return None
                
                s = str(pgrr.a['href']).split('=')
                lastpage = int(s[-1]) 

                for page in range(1, lastpage+1):       # 뉴스 링크의 페이지 별로 실행
                    pg_url = f'{var.NEWS_URL}&date={date}&page={page}'      
                    html = BeautifulSoup(requests.get(url=pg_url, headers=var.HEADERS).text,'lxml') 

                    # 뉴스 링크, 제목을 포함하는 dd, dt 총 2개로 나누어져 있음. 둘다 가져오기
                    news_dd = html.find_all('dd', class_='articleSubject')
                    news_dt = html.find_all('dt', class_='articleSubject')
                    # news summary, newspaper company name은 dd로만 있음
                    news_summary = html.find_all('dd', class_='articleSummary')
                    print(f'[{date}] {int(page):02d}/{int(lastpage):02d} downloading...', end='\r')     

                    for tag in news_dd + news_dt:     
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
                exception_data = {          # 날짜, 오류의 이유를 json 형식으로 만들어서 저장. 
                    'date': date,         
                    'error_code':str(e)
                }

                try:
                    with open('json\\exception_news.json', 'r') as json_file: 
                        existing_data = json.load(json_file)
                        existing_data['data'].append(exception_data)
                    
                    with open('json\\exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

                except FileNotFoundError:      
                    existing_data = {'data': [exception_data]}
                    with open('json\\exception_news.json', 'w') as json_file:
                        json.dump(existing_data, json_file)

            NewsDF = pd.concat([NewsDF, day_DF], ignore_index=True)
            date = (datetime.strptime(date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')       # 다음날로 넘어감
        print()
        return NewsDF
    
    def getArticleText(self, url) -> str or None:
        """
        뉴스 기사를 str 형식으로 찾아서 제공함.

        만약, 오류가 나는 경우, None을 return하여 ```papago``` 의 실행이 되지 않게 함 
        """
        response = requests.get(url, headers=var.HEADERS)

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            for div in soup.find_all("div",class_="link_news"):
                div.decompose()
            news_article = soup.find_all("div", class_="articleCont")
            if news_article:
                combined_article_text = ''
                for article_cont in news_article:
                    article_text = article_cont.get_text(separator=' ')
                    combined_article_text += article_text + '\n'
            
            return combined_article_text
            
        except Exception as e:
            exception_data = {
                'url': url,
                'error_code': str(e)
            }
            try:
                with open('json\\exception_news_text.json', 'r') as json_file: # exception_news.json에 오류 data 저장
                    existing_data = json.load(json_file)
                    existing_data['data'].append(exception_data)
                
                with open('json\\exception_news_text.json', 'w') as json_file:
                    json.dump(existing_data, json_file)

            except FileNotFoundError:       # exception_news.json이 없으면 새로 만들어서 저장
                existing_data = {'data': [exception_data]}
                with open('json\\exception_news_text.json', 'w') as json_file:
                    json.dump(existing_data, json_file)

            return None

    
    def papagoJsonReset(self) -> json.dump:
        """
        papgo_api.json이 하루마다 초기화되기 때문에, 그 정보를 바탕으로 설정

        매일 한번 번역 사용 전, 실행해주면 됨
        """
        today = datetime.now().date()
        with open('json\\papago_api.json', 'r') as json_file:
            papago_api = json.load(json_file)
            data = papago_api["data"]
            _appIds = list(data.keys())

            for _appId in _appIds:
                _appId_date = papago_api["data"][_appId]["Latest_Date"]
                _appId_date = datetime.strptime(_appId_date, "%Y-%m-%d").date()
                if today > _appId_date:
                    papago_api["data"][_appId]["Latest_Date"] = str(today)
                    papago_api["data"][_appId]["Limit"] = 0
            
        with open('json\\papago_api.json', 'w') as json_file:
            json.dump(papago_api, json_file, indent=4)

        print('papago_api.json Reset Ok')

    def getPapagoAPIKey(self, article) -> (json.dump and str) or None:
        """
        article의 길이에 맞는 적절한 api key 받아옴.

        이후, ```usePapagoAPI```를 호출하여 번역 작업 실행 후 그에 해당하는 값 받아옴

        마지막으로, papago_api.json의 limit 값 반영하여 저장함.
        """
        article_len = len(str(article))
        if article_len < 10:
            return None         # might be None(len: 4) or wrong msg.
        with open('json\\papago_api.json', 'r') as json_file:
            papago_api = json.load(json_file)
            data = papago_api["data"]
            _appIds = list(data.keys())

            for _appId in _appIds:
                limit = papago_api["data"][_appId]["Limit"]

                if 10000 > limit + article_len:     # daily limit is 10,000(Naver PAPAGO)
                    client_id = papago_api["data"][_appId]["Client_ID"]
                    client_secret = papago_api["data"][_appId]["Client_Secret"]
                    break

        translated_text = self.usePapagoAPI(article, client_id, client_secret)
        
        if translated_text is not None:
            papago_api["data"][_appId]["Limit"] += article_len
            with open('json\\papago_api.json', 'w') as json_file:
                json.dump(papago_api, json_file, indent=4)

        return translated_text


    def usePapagoAPI(self, article, client_id, client_secret) -> str:
        """
        article을 받으면 papago api를 호출하여 번역 실행. 
        
        번역된 텍스트를 전달함
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret
        }
        data = {'source': 'ko', 'target': 'en', 'text': article}
        response = requests.post(var.PAPAGO_URL, json.dumps(data), headers=headers)
        if response == 200:
            en_text = response.json()["message"]["result"]["translatedText"]
            return en_text
        return None

    def getridOfTitles(self, title=str) -> pd.DataFrame:
        """
        From 

        ```python 
        def getNewsByDate
        ```
        get ```NewsDF```, 필요없는 내용 삭제, 특수문자 치환하는 함수
        """
        # title + News_chg.json["change"]
        # ex. 한자, 영어 -> 회사 이름 파악용
        with open('json\\News_chg.json', 'r') as json_file:
            chg = json_file["change"]
            chg_key = list(chg.keys())
            for chg_data in chg_key:
                if title.find(chg_data) != -1:
                    title.replace(chg_data, chg["change"][chg_data])
        return title
            


    def getFormattedDate(self, date=None) -> str:
        """
        - date : format 안된 date를 getNewsByDate에서 실행할 수 있게 적절히 변환.

        None일 경우, 오늘의 날짜로 변경

        return date(string) -> example : "20230911"
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
    getNewsActivate.papagoJsonReset()