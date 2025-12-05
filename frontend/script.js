// 課程時間對照表
const periods = [
    { period: '1', time: '08:00-08:50' },
    { period: '2', time: '09:00-09:50' },
    { period: '3', time: '10:00-10:50' },
    { period: '4', time: '11:00-11:50' },
    { period: 'N', time: '12:00-13:00' },
    { period: '5', time: '13:00-13:50' },
    { period: '6', time: '14:00-14:50' },
    { period: '7', time: '15:00-15:50' },
    { period: '8', time: '16:00-16:50' },
    { period: '9', time: '17:00-17:50' },
    { period: 'A', time: '18:00-18:50' },
    { period: 'B', time: '19:00-19:50' },
    { period: 'C', time: '20:00-20:50' },
    { period: 'D', time: '21:00-21:50' },
    { period: 'E', time: '22:00-22:50' },
    { period: 'F', time: '23:00-23:50' }
];

const weekdays = ['一', '二', '三', '四', '五'];


// 狀態管理
let busyTimes = new Set(); // 記錄忙碌時間（沒空的時間）
let selectedCourses = new Set(); // 記錄選中的課程流水號

// 虛擬滾動相關變數
let allCourses = []; // 所有篩選後的課程
let rowHeight = 70; // 每行的高度（像素）
let visibleRowCount = 12; // 可見行數
let bufferRowCount = 3; // 緩衝行數
let currentScrollTop = 0;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeWeekdayDropdowns();
    setupEventListeners();
});

// 建立週次選單的下拉項目（可點選）
function initializeWeekdayDropdowns() {
    weekdays.forEach((day, dayIndex) => {
        const container = document.getElementById(`day-${dayIndex + 1}`);
        
        periods.forEach(period => {
            const periodItem = document.createElement('div');
            periodItem.className = 'period-item';
            periodItem.dataset.day = dayIndex + 1;
            periodItem.dataset.period = period.period;
            
            const periodLabel = document.createElement('span');
            periodLabel.textContent = `第${period.period}節`;
            
            const periodTime = document.createElement('span');
            periodTime.className = 'period-time';
            periodTime.textContent = period.time;
            
            periodItem.appendChild(periodLabel);
            periodItem.appendChild(periodTime);
            
            // 點擊切換選中狀態
            periodItem.addEventListener('click', function() {
                this.classList.toggle('selected');
                updateBusyTimes();
            });
            
            container.appendChild(periodItem);
        });
    });
}

// 設定事件監聽器
function setupEventListeners() {
    // 週次展開/收合
    document.querySelectorAll('.weekday-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const day = this.dataset.day;
            const content = document.getElementById(`day-${day}`);
            const isVisible = content.style.display !== 'none';
            
            if (isVisible) {
                content.style.display = 'none';
                this.classList.remove('active');
            } else {
                content.style.display = 'block';
                this.classList.add('active');
            }
        });
    });
    
    
    // 搜尋按鈕
    document.getElementById('searchBtn').addEventListener('click', searchCourses);

    // 下載按鈕
    document.getElementById('downloadBtn').addEventListener('click', downloadSelectedCourses);

    // 全選複選框
    document.getElementById('selectAllCheckbox').addEventListener('change', toggleSelectAll);

    // 虛擬滾動監聽
    const tableBodyWrapper = document.getElementById('tableBodyWrapper');
    if (tableBodyWrapper) {
        tableBodyWrapper.addEventListener('scroll', handleVirtualScroll);
    }
}

// 更新忙碌時間
function updateBusyTimes() {
    busyTimes.clear();
    document.querySelectorAll('.period-item.selected').forEach(item => {
        const day = item.dataset.day;
        const period = item.dataset.period;
        busyTimes.add(`${day}-${period}`);
    });
}

// 搜尋課程 - 發送請求到後端
async function searchCourses() {
    updateBusyTimes();

    // 收集篩選條件
    const department = document.getElementById('userDepartment')?.value.trim() || '';
    const grade = document.getElementById('userGrade')?.value || '1';

    // 將 busyTimes Set 轉換為陣列
    const busyTimesArray = Array.from(busyTimes);

    // 準備請求資料
    const requestData = {
        department: department,
        grade: parseInt(grade),
        busyTimes: busyTimesArray
    };

    // 顯示載入中
    const tableBody = document.getElementById('courseTableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="loading-cell">⏳ 正在搜尋課程...</td>
        </tr>
    `;

    try {
        // 發送 POST 請求到後端
        const response = await fetch(`${API_BASE_URL}/api/filter-courses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // 顯示結果
        displayResults(data.courses || []);

    } catch (error) {
        console.error('搜尋課程時發生錯誤:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="loading-cell">❌ 搜尋失敗：${error.message}<br>請確認後端伺服器是否正在運行</td>
            </tr>
        `;
    }
}


// 顯示結果
function displayResults(courses) {
    allCourses = courses;
    selectedCourses.clear();
    const courseCount = document.getElementById('courseCount');
    const resultCount = document.getElementById('resultCount');
    const downloadBtn = document.getElementById('downloadBtn');

    courseCount.textContent = courses.length;

    if (courses.length === 0) {
        const tableBody = document.getElementById('courseTableBody');
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="loading-cell">😔 沒有找到符合條件的課程，試著取消一些忙碌時段吧！</td>
            </tr>
        `;
        resultCount.style.display = 'none';
        downloadBtn.style.display = 'none';

        document.getElementById('tableBodySpacer').style.height = '0px';
    } else {
        resultCount.style.display = 'block';
        downloadBtn.style.display = 'block';

        initVirtualScroll();
    }
}

function toggleSelectAll(event) {
    const isChecked = event.target.checked;
    selectedCourses.clear();

    if (isChecked) {
        allCourses.forEach(course => {
            selectedCourses.add(course.code);
        });
    }

    renderVisibleRows();
    updateDownloadButton();
}

function updateDownloadButton() {
    const downloadBtn = document.getElementById('downloadBtn');
    const count = selectedCourses.size;

    if (count > 0) {
        downloadBtn.textContent = `下載選中課程 (${count})`;
        downloadBtn.disabled = false;
    } else {
        downloadBtn.textContent = '下載選中課程';
        downloadBtn.disabled = true;
    }
}

async function downloadSelectedCourses() {
    if (selectedCourses.size === 0) {
        alert('請先選擇要下載的課程');
        return;
    }

    const downloadBtn = document.getElementById('downloadBtn');
    const originalText = downloadBtn.textContent;
    downloadBtn.textContent = '⏳ 正在準備下載...';
    downloadBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/api/download-courses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                courseCodes: Array.from(selectedCourses)
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'selected_courses.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert(`成功下載 ${selectedCourses.size} 門課程！`);
    } catch (error) {
        console.error('下載課程時發生錯誤:', error);
        alert(`下載失敗：${error.message}`);
    } finally {
        downloadBtn.textContent = originalText;
        downloadBtn.disabled = false;
    }
}

// 初始化虛擬滾動
function initVirtualScroll() {
    const tableBodyWrapper = document.getElementById('tableBodyWrapper');
    const tableBodySpacer = document.getElementById('tableBodySpacer');
    
    // 設置總高度
    const totalHeight = allCourses.length * rowHeight;
    tableBodySpacer.style.height = `${totalHeight}px`;
    
    // 重置滾動位置
    tableBodyWrapper.scrollTop = 0;
    currentScrollTop = 0;
    
    // 渲染初始可見項目
    renderVisibleRows();
}

// 處理虛擬滾動
function handleVirtualScroll() {
    const tableBodyWrapper = document.getElementById('tableBodyWrapper');
    const newScrollTop = tableBodyWrapper.scrollTop;
    
    // 只有滾動超過一定距離才重新渲染
    if (Math.abs(newScrollTop - currentScrollTop) > rowHeight / 2) {
        currentScrollTop = newScrollTop;
        renderVisibleRows();
    }
}

// 渲染可見的行
function renderVisibleRows() {
    const tableBodyWrapper = document.getElementById('tableBodyWrapper');
    const tableBody = document.getElementById('courseTableBody');
    const scrollTop = tableBodyWrapper.scrollTop;
    
    // 計算可見範圍
    const startIndex = Math.floor(scrollTop / rowHeight);
    const endIndex = Math.min(
        startIndex + visibleRowCount + bufferRowCount,
        allCourses.length
    );
    
    // 計算實際開始索引（包含緩衝）
    const actualStartIndex = Math.max(0, startIndex - bufferRowCount);
    
    // 計算偏移量
    const offsetY = actualStartIndex * rowHeight;
    
    // 清空並重新渲染
    tableBody.innerHTML = '';
    
    for (let i = actualStartIndex; i < endIndex; i++) {
        const course = allCourses[i];
        const row = createCourseRow(course, i);
        tableBody.appendChild(row);
    }
    
    // 設置表格位置
    tableBody.parentElement.style.transform = `translateY(${offsetY}px)`;
}

// 建立課程表格行
function createCourseRow(course, index) {
    const row = document.createElement('tr');
    const isChecked = selectedCourses.has(course.code);

    row.innerHTML = `
        <td><input type="checkbox" class="course-checkbox" data-code="${course.code}" ${isChecked ? 'checked' : ''}></td>
        <td>${index}</td>
        <td>
            <div class="course-name">${course.name}</div>
            <div class="course-code">${course.code}</div>
            ${course.note ? `<div class="course-note">${course.note}</div>` : ''}
        </td>
        <td>${course.teacher}</td>
        <td>${course.credits}</td>
        <td>
            <div style="margin-bottom: 4px;"><strong>${formatTimeDisplay(course.time)}</strong></div>
            <div style="color: #888; font-size: 0.85em;">${course.classroom}</div>
        </td>
        <td>${course.type}</td>
        <td>${course.semester}</td>
    `;

    const checkbox = row.querySelector('.course-checkbox');
    checkbox.addEventListener('change', function() {
        if (this.checked) {
            selectedCourses.add(course.code);
        } else {
            selectedCourses.delete(course.code);
        }
        updateDownloadButton();
    });

    return row;
}

// 格式化時間顯示
function formatTimeDisplay(timeString) {
    // 將 "一234" 轉換為 "週一 2,3,4"
    const parts = timeString.split(',');
    return parts.map(part => {
        const match = part.match(/([一二三四五])([0-9NABCDEF]+)/);
        if (match) {
            const day = match[1];
            const periods = match[2].split('').join(',');
            return `週${day} ${periods}`;
        }
        return part;
    }).join(' / ');
}
