url = '/news/news_read.naver?article_id=0007028727&office_id=421&mode=LSS2D&type=0&section_id=101&section_id2=258&section_id3=&date=20230905&page=23'

# URL 문자열을 & 문자를 기준으로 분할합니다.
url = url.split('?')[-1]
params = url.split('&')

# 분할된 문자열에서 필요한 값을 추출합니다.
article_id = None
office_id = None
date = None
page = None

for param in params:
    key, value = param.split('=')
    if key == 'article_id':
        article_id = value
    elif key == 'office_id':
        office_id = value
    elif key == 'date':
        date = value
    elif key == 'page':
        page = value

print("article_id:", article_id)
print("office_id:", office_id)
print("date:", date)
print("page:", page)
