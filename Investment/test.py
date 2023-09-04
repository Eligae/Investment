from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

# 크롬 드라이버로 웹 페이지 열기
driver = webdriver.Chrome()
driver.get("https://finance.naver.com/item/sise.naver?code=005930")

try:
    wrapper = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'pgRR'))
    )
    link_element = wrapper.find_element_by_tag_name('a')
    link = link_element.get_attribute('href')
    print(link)
except TimeoutException:
    print("time out!")

driver.quit()