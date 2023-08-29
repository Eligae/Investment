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