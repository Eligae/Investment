# Investment module
매일 17 : 00 에 실행하도록 설정하기

## DBUpdater.bat 설정


```txt
python <file 경로 설정>\DBUpdater.py
```
위의 코드 입력 후, 저장. 

1. win + R에서 regedit입력 -> 레지스트리 편집 실행
2. ```HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run``` 검색

    ![image](./readme_img/run_register.png)

3. Run 폴더 마우스 우클릭
4. 새로만들기 메뉴
5. 문자열 값 메뉴 클릭
6. ```DBUPDATER```라는 문자열 값으로 **DBUpdater.bat**경로 지정

자동으로 실행 적용 완료

## 예상
```Investment/```에서 사용할 함수(Library) 작성중..

1. Analyzer.py : MariaDB에서 Data 호출 용

2. DBUpdater.py : [Naver 금융](https://finance.naver.com)에서 회사 별 주식 등락 폭 등 다양한 정보 Crawling이후, MariaDB에 저장
3. getFinanceNews.py : [Naver 금융 뉴스](https://finance.naver.com/news/)에서 실시간 부분에서 뉴스 제목, 내용 Crawling
4. konlpy_News.py : getFinanceNews.py에서 얻어온 News 내용 분석, MariaDB에 저장
5. var.py : MariaDB, request headers, url 등 정보 저장 용도 

## 분석 기법 example

1. 현대 포트폴리오 이론 : Portfolio selection - by.Harry Max Markowitz(1952)
>평균-분산 최적화(mean-variance optimization, MVO)는 예상 수익률과 리스크의 상관관계를 활용해 포트폴리오를 최적화하는 기법.
>- 수익률과 표준편차
<br>
>- 효율적 투자선(Efficiant Frontier) : [Code - 몬테카를로_시뮬레이션]()