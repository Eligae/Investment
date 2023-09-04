from bs4 import BeautifulSoup
import requests
import var

class getNews:
    def __init__(self):
        """생성자 : 기본 url 주소를 받아옴"""
        self.url = var.NEWS_URL
    
    def __del__(self):
        """소멸자 : pass"""
        pass
    
    def getNewsByDate(self, date):
        """
        - date : format as '20230901'. then, url = url + '&date={date}'
        날짜를 받아와서 해당 날에 대한 finance.naver의 주소 구하고, 크롤링 실행
        return DataFrame
        """
        

    def getFormattedDate(self, date):
        """
        - date : format 안된 date를 getNewsByDate에서 실행할 수 있게 적절히 변환.
        return date(string)
        """
    
    def activate(self, date=0):
        """
        - 실제로 실행할 기간 정함. default = 0 이면 현재 날만 실행
        - 만약 특정 날 입력 시, 그 날부터 현재까지 getNewsByDate 실행함.
        """
        
if __name__ == "__main__":
    getNewsActivate = getNews()
    getNews.activate()