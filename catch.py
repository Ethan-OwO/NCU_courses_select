import requests
from bs4 import BeautifulSoup
import urllib3
import time
import random
import pandas as pd
import re

# --- 1. 基礎設定 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 偽裝成台灣繁體中文使用者的瀏覽器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

# 設定你指定的 10 個欄位名稱
columns = [
    "流水號", "名稱與備註", "教授", "學分", "時間與教室", 
    "選修別", "全與半", "人數限制", "分發條件連結", "課程綱要連結"
]

all_courses = []

print("開始精準爬取，目標：1-43 頁...")

# --- 2. 爬取迴圈 (1 到 43 頁) ---
for page in range(1, 44):
    print(f"[{page}/43] 正在處理...", end="")
    
    try:
        # 網址參數說明：d-49489-p 是頁碼，crs_lang_no=1 強制中文
        url = f'https://cis.ncu.edu.tw/Course/main/query/byKeywords?week=&year=114&selectDept=&d-49489-p={page}&query=%E6%9F%A5%E8%A9%A2&fall_spring=2&keyword=&day=&crs_lang_no=1'
        
        response = requests.get(url, verify=False, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr', class_=['odd', 'even'])
            
            page_count = 0
            for row in rows:
                cols = row.find_all('td')
                
                # 確保這一行真的有 10 格 (避免抓到奇怪的排版)
                if len(cols) == 10:
                    row_data = []
                    
                    # --- 前 8 格：直接抓文字 ---
                    # 包含：流水號, 名稱, 教授, 學分, 時間, 選修, 全半, 人數
                    for i in range(8):
                        text = cols[i].get_text(strip=True)
                        row_data.append(text)
                    
                    # --- 第 9 格：分發條件 (抓連結) ---
                    limit_html = cols[8].find('a')
                    limit_url = ""
                    if limit_html and 'onclick' in limit_html.attrs:
                        # 抓出 open_limit('/Course/...') 裡面的路徑
                        match = re.search(r"open_limit\('([^']+)'\)", limit_html['onclick'])
                        if match:
                            limit_url = "https://cis.ncu.edu.tw" + match.group(1)
                    row_data.append(limit_url)
                    
                    # --- 第 10 格：課程綱要 (抓連結) ---
                    outline_html = cols[9].find('a')
                    outline_url = ""
                    if outline_html and 'onclick' in outline_html.attrs:
                        # 抓出 open_outline('/Course/...') 裡面的路徑
                        match = re.search(r"open_outline\('([^']+)'\)", outline_html['onclick'])
                        if match:
                            outline_url = "https://cis.ncu.edu.tw" + match.group(1)
                    row_data.append(outline_url)
                    
                    # 加入總表
                    all_courses.append(row_data)
                    page_count += 1
            
            print(f" 成功取得 {page_count} 筆")
        else:
            print(f" 失敗 (Status: {response.status_code})")
            
    except Exception as e:
        print(f" 錯誤: {e}")

    # 禮貌性暫停，避免被鎖 IP
    time.sleep(random.uniform(0.8, 1.5))

# --- 3. 輸出漂亮的 Excel (含防呆機制) ---
print(f"\n爬取結束，共 {len(all_courses)} 筆資料，正在寫入 Excel...")

df = pd.DataFrame(all_courses, columns=columns)

# 這裡將檔案存為 "中央大學選課表_完整版.xlsx"
output_file = "中央大學選課表_完整版.xlsx"

try:
    # 嘗試存成 Excel
    df.to_excel(output_file, index=False)
    print(f"完成！檔案已儲存為：{output_file}")

except ModuleNotFoundError:
    print("【存檔失敗】缺少 'openpyxl' 套件，無法存成 Excel。")
    print("請在終端機執行: pip install openpyxl")
    print("正在為您改存成 CSV 檔，以免資料遺失...")
    
    # 備案：存成 CSV (utf-8-sig 可以讓 Excel 正確顯示中文)
    df.to_csv("中央大學選課表_完整版.csv", index=False, encoding="utf-8-sig")
    print("已成功備份為：中央大學選課表_完整版.csv")

except Exception as e:
    print(f"存檔發生其他錯誤: {e}")
    print("正在為您改存成 CSV 檔...")
    df.to_csv("中央大學選課表_完整版.csv", index=False, encoding="utf-8-sig")
    print("已成功備份為：中央大學選課表_完整版.csv")