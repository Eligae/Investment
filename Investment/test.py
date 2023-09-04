from bs4 import BeautifulSoup
import requests

def get_th_values(code):
    url = f'https://finance.naver.com/item/main.naver?code={code}'
    html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, "lxml")
    
    # <div class="section cop_analysis"> 요소를 찾습니다.
    cop_analysis_div = html.find('div', class_='section cop_analysis')
    
    if cop_analysis_div:
        # 해당 <th> 요소들을 모두 찾습니다.
        th_elements = cop_analysis_div.select('table.tb_type1_ifrs th')
        
        # 각 <th> 요소의 텍스트 값을 가져와서 리스트에 저장합니다.
        th_values = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        return th_values
    else:
        return None

# 코드를 호출하여 <th> 요소들의 값을 가져옵니다.
th_values = get_th_values("001470")
if th_values:
    for value in th_values:
        print(value)
else:
    print("주요재무정보를 찾을 수 없습니다.")
