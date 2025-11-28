import requests
from bs4 import BeautifulSoup
import urllib3 # 匯入這個是為了隱藏紅色的警告訊息

# 1. 禁用 SSL 警告 (讓程式畫面乾淨一點)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://cis.ncu.edu.tw/Course/main/query/byKeywords?week=&year=114&selectDept=&d-49489-p=3&query=%E6%9F%A5%E8%A9%A2&fall_spring=2&keyword=&day=&crs_lang_no=0'  # 這是你報錯訊息中的網址

# 2. 加入 verify=False 參數，跳過憑證檢查
try:
    # headers 是為了模擬瀏覽器，有些學校網站會擋沒有 headers 的爬蟲
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 關鍵修改在這裡： verify=False
    response = requests.get(url, verify=False, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        print("成功連線！網頁標題:", soup.title.string)
        # 接續你原本要做的爬蟲邏輯...
    else:
        print(f"連線失敗，狀態碼: {response.status_code}")

except Exception as e:
    print(f"發生錯誤: {e}")