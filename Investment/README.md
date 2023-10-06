# Library : Investment
## Structure
|file name|work|
|--|--|
|DBUpdater.py|1. Maria DB의 **company info**<br> 2. 96.6.25 ~ 현재의 **ohlcv 표** 저장
|getFinanceNews.py|finance.naver.com의 실시간 속보 제목, link 추출. 중요한 내용일 경우 추가적 분석 들어갈듯.|
|Analyzer.py|Maria DB의 데이터를 query를 통해 가져오는 함수 내장|
|var.py|다양한 file에서 사용될 상수, URL 등 정보 저장|

