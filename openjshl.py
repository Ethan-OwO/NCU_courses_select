import pandas as pd
import requests
import urllib3
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # 進度條

# --- 1. 基礎設定 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定 Headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
}

# 建立 Session 加速連線
session = requests.Session()
session.headers.update(headers)
session.verify = False

# 輸入與輸出檔名
input_file = "中央大學選課表_完整版.xlsx"
output_file = "中央大學課程詳情_最終版.xlsx"

# --- 2. 抓取內容的函數 (工讀生做的事) ---
def fetch_text_from_url(url):
    """
    給網址，回傳網頁內的純文字
    """
    if pd.isna(url) or url == "" or not str(url).startswith("http"):
        return "" # 如果網址是空的，直接回傳空字串
    
    try:
        # 隨機休息極短時間，稍微錯開請求
        time.sleep(random.uniform(0.05, 0.2))
        
        # 設定 timeout 避免卡死
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            # 這裡因為我們沒有引入 bs4 在這個函數內，需要 import
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 抓取 body 文字，用換行符號分隔
            text = soup.body.get_text(separator='\n', strip=True)
            
            # 清理過多的連續換行
            import re
            text = re.sub(r'\n+', '\n', text)
            
            # Excel 單一儲存格最多 32767 字元，截斷以防萬一
            return text[:30000]
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return "連線失敗"

# --- 3. 主程式 ---
def main():
    print(f"正在讀取 Excel 檔案: {input_file} ...")
    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print(f"找不到檔案！請確認資料夾內是否有 '{input_file}'")
        return

    print(f"讀取成功！共有 {len(df)} 筆資料。")

    # 檢查 Excel 欄位名稱是否正確 (根據上一段程式碼的設定)
    required_cols = ["分發條件連結", "課程綱要連結"]
    for col in required_cols:
        if col not in df.columns:
            print(f"錯誤：Excel 裡找不到欄位 '{col}'，請檢查欄位名稱。")
            return

    # 建立新欄位來放結果
    # 如果原本沒有這些欄位，先初始化為空字串
    if "分發條件內容" not in df.columns:
        df["分發條件內容"] = ""
    if "課程綱要內容" not in df.columns:
        df["課程綱要內容"] = ""

    print("=== 開始多執行緒爬取詳細內容 ===")
    print("這可能需要幾分鐘，請耐心等待進度條跑完...")

    # 收集所有的任務
    # 格式: (DataFrame的索引 index, 目標欄位名稱, 網址)
    tasks = []
    
    for index, row in df.iterrows():
        # 任務 1: 分發條件
        url_limit = row["分發條件連結"]
        if pd.notna(url_limit) and str(url_limit).startswith("http"):
            tasks.append((index, "分發條件內容", url_limit))
            
        # 任務 2: 課程綱要
        url_outline = row["課程綱要連結"]
        if pd.notna(url_outline) and str(url_outline).startswith("http"):
            tasks.append((index, "課程綱要內容", url_outline))

    # 使用 ThreadPoolExecutor 進行併發抓取
    # max_workers=10 代表同時開 10 個連線 (視學校網站承受力調整，建議 5~10)
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有任務
        future_to_task = {
            executor.submit(fetch_text_from_url, task[2]): (task[0], task[1]) 
            for task in tasks
        }
        
        # 使用 tqdm 顯示進度條
        for future in tqdm(as_completed(future_to_task), total=len(tasks), unit="link"):
            idx, col_name = future_to_task[future]
            try:
                result_text = future.result()
                # 將結果寫回 DataFrame
                df.at[idx, col_name] = result_text
            except Exception as e:
                df.at[idx, col_name] = "抓取發生未知錯誤"

    print("\n抓取完成！正在儲存新的 Excel...")
    
    # 調整欄位順序 (把內容放在連結後面，方便閱讀)
    # 這裡建立一個理想的順序列表
    final_columns = [
        "流水號", "名稱與備註", "教授", "學分", "時間與教室", 
        "選修別", "全與半", "人數限制", 
        "分發條件內容", "課程綱要內容", # 把內容往前放
        "分發條件連結", "課程綱要連結"
    ]
    
    # 確保只選取存在的欄位 (避免報錯)
    cols_to_save = [c for c in final_columns if c in df.columns]
    df = df[cols_to_save]

    try:
        df.to_excel(output_file, index=False)
        print(f"成功！完整檔案已儲存為：{output_file}")
    except Exception as e:
        print("存成 Excel 失敗 (可能是檔案被打開了？)，改存 CSV...")
        df.to_csv(output_file.replace(".xlsx", ".csv"), index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()