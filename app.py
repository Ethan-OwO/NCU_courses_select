import streamlit as st
import pandas as pd
import re

# --- 1. 網頁設定 ---
st.set_page_config(
    page_title="NCU 選課小幫手",
    page_icon="🎓",
    layout="wide"
)

# --- 2. 讀取資料 (使用 Cache 加速，不用每次重新讀取) ---
@st.cache_data
def load_data():
    # 這裡請確認你的檔案名稱，建議統一轉成 csv 讀取比較快，也可以用 read_excel
    # 假設你的檔案叫做 'courses.csv'
    try:
        df = pd.read_csv("courses.csv") # 如果是 xlsx 請改用 pd.read_excel("courses.xlsx")
        
        # 簡單的資料清理：把 NaN (空值) 補成空字串
        df.fillna("", inplace=True)
        return df
    except FileNotFoundError:
        return None

# --- 3. 核心邏輯：時間解析器 ---
def parse_time_string(time_str):
    """
    將 '一234/TR-A001' 或 '1-34,3-CD' 轉換成標準集合
    回傳格式範例: {('Mon', '2'), ('Mon', '3'), ('Mon', '4')}
    """
    if not isinstance(time_str, str):
        return set()

    # 定義星期對照
    day_map = {
        '1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu', '5': 'Fri', '6': 'Sat', '7': 'Sun',
        '一': 'Mon', '二': 'Tue', '三': 'Wed', '四': 'Thu', '五': 'Fri', '六': 'Sat', '日': 'Sun'
    }
    
    # 定義節次集合 (中央大學代碼)
    valid_periods = set("123456789ABCDEFZ")
    
    occupied_slots = set()
    
    # 步驟 A: 先把地點切掉 (用 / 或 [ 切割)
    # '一234/TR-A001' -> '一234'
    clean_str = re.split(r'[/\[]', time_str)[0]
    
    # 步驟 B: 分割多個時段 (用逗號切割)
    # '1-34,3-CD' -> ['1-34', '3-CD']
    parts = clean_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part: continue
        
        # 抓取第一個字當作星期
        first_char = part[0]
        if first_char in day_map:
            day_code = day_map[first_char]
            # 剩下的字串視為節次
            periods = part[1:].replace("-", "") # 去掉中間的橫線
            
            for p in periods:
                if p in valid_periods:
                    occupied_slots.add((day_code, p))
                    
    return occupied_slots

# --- 4. 主程式介面 ---
def main():
    st.title("🎓 NCU 中央大學選課篩選器")
    st.markdown("輸入你的空堂時間與系級，快速找出能上的課！")

    # 讀取資料
    df = load_data()
    
    if df is None:
        st.error("❌ 找不到資料檔！請確認資料夾內是否有 'courses.csv' (或 .xlsx)。")
        st.info("💡 提示：請將爬蟲抓下來的檔案改名，並放在與此程式同一層目錄。")
        return

    # --- 側邊欄：使用者設定 ---
    with st.sidebar:
        st.header("1. 個人設定")
        
        # 系所關鍵字篩選
        dept_input = st.text_input("你的系所 (用於過濾限修)", placeholder="例如：資工系, 通訊系")
        
        # 年級篩選
        grade_level = st.selectbox("你的年級", ["大一", "大二", "大三", "大四", "碩/博"])
        
        st.divider()
        st.header("2. 設定「沒空」的時間")
        st.caption("請勾選你 **已經有課** 或 **不想排課** 的時段：")
        
        # 建立時間選擇器
        user_busy_slots = set()
        days = {'Mon': '週一', 'Tue': '週二', 'Wed': '週三', 'Thu': '週四', 'Fri': '週五'}
        periods = list("123456789ABCD") # 簡化的節次列表
        
        # 使用 Expander 收折每一天，讓介面乾淨點
        for day_code, day_name in days.items():
            with st.expander(f"{day_name} (點擊展開)"):
                selected_periods = st.multiselect(
                    f"選擇 {day_name} 沒空的的節次:",
                    periods,
                    key=f"busy_{day_code}"
                )
                for p in selected_periods:
                    user_busy_slots.add((day_code, p))

        run_filter = st.button("🔍 開始篩選", type="primary")

    # --- 右側：結果顯示區 ---
    if run_filter:
        with st.spinner("正在分析 2000+ 堂課程..."):
            
            results = []
            
            # 遍歷每一堂課進行篩選
            for index, row in df.iterrows():
                # 1. 解析這堂課的時間
                course_time_str = str(row.get('時間與教室', ''))
                course_slots = parse_time_string(course_time_str)
                
                # 2. 檢查衝堂 (交集運算)
                # 如果 (課程時間) 和 (使用者沒空時間) 有交集 -> 衝堂
                is_conflict = not course_slots.isdisjoint(user_busy_slots)
                
                if is_conflict:
                    continue # 衝堂了，跳過
                
                # 3. 檢查系級/分發條件 (簡單關鍵字過濾)
                # 這裡做「防守型」過濾：只有明確寫了「限XX」且你不符合才過濾
                limit_text = str(row.get('分發條件內容', ''))
                status = "✅ 可選"
                note = ""

                # 簡單的邏輯範例：
                # 如果分發條件寫 "限大四"，但你是 "大一" -> 排除
                # (這部分正規表達式比較難完美，我們先做基礎標記)
                if "限大四" in limit_text and grade_level != "大四":
                     status = "⚠️ 需確認 (年級)"
                
                # 如果有輸入系所，且限制條件提到別的系 -> 標記
                # 例如：你是資工，條件寫「限企管系」
                if dept_input and "限" in limit_text:
                    # 這邊邏輯比較複雜，暫時僅標記提醒，不做硬性刪除，避免誤刪通識
                    note = "請確認分發條件"

                # 整理要顯示的資料
                results.append({
                    "課程名稱": row.get('名稱與備註', ''),
                    "時間": row.get('時間與教室', ''),
                    "教授": row.get('教授', ''),
                    "選修別": row.get('選修別', ''),
                    "狀態": status,
                    "分發條件": limit_text,
                    "連結": row.get('分發條件連結', '') # 這裡保留連結
                })
            
            # --- 顯示結果 ---
            if results:
                result_df = pd.DataFrame(results)
                
                st.success(f"找到 {len(result_df)} 堂適合的課程！")
                
                # 使用 Streamlit 的強大表格顯示，支援連結點擊
                st.dataframe(
                    result_df,
                    column_config={
                        "連結": st.column_config.LinkColumn("分發連結"), # 把網址變成可點擊的按鈕
                        "課程名稱": st.column_config.TextColumn("課程名稱", width="medium"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("嗚嗚，找不到符合條件的課。試著減少一點「沒空」的時間？")

    else:
        # 預設畫面
        st.info("👈 請在左側側邊欄輸入條件，然後按下「開始篩選」！")
        
        # 顯示原始資料預覽
        st.subheader("目前課程資料庫預覽")
        st.dataframe(df.head(10), use_container_width=True)

if __name__ == "__main__":
    main()


### 如何在你的電腦上執行 (測試)
