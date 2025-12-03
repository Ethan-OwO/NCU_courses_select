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
    { period: 'A', time: '18:30-19:20' },
    { period: 'B', time: '19:25-20:15' },
    { period: 'C', time: '20:20-21:10' },
    { period: 'D', time: '21:15-22:05' }
];

const weekdays = ['一', '二', '三', '四', '五'];

// 擴充的課程資料
const courses = [
];

// 狀態管理
let busyTimes = new Set(); // 改為記錄忙碌時間（沒空的時間）
let currentFilters = {
    department: '',
    grade: '1'
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeWeekdayCheckboxes();
    setupEventListeners();
});

// 建立週次選單的checkbox
function initializeWeekdayCheckboxes() {
    weekdays.forEach((day, dayIndex) => {
        const container = document.getElementById(`day-${dayIndex + 1}`);
        
        periods.forEach(period => {
            const checkboxItem = document.createElement('div');
            checkboxItem.className = 'checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `period-${dayIndex + 1}-${period.period}`;
            checkbox.dataset.day = dayIndex + 1;
            checkbox.dataset.period = period.period;
            
            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = `第${period.period}節 (${period.time})`;
            
            checkboxItem.appendChild(checkbox);
            checkboxItem.appendChild(label);
            container.appendChild(checkboxItem);
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
    
    // Checkbox 變更
    document.querySelectorAll('.period-checkboxes').forEach(container => {
        container.addEventListener('change', function(e) {
            if (e.target.type === 'checkbox') {
                updateBusyTimes();
            }
        });
    });
    
    // 個人設定變更
    document.getElementById('userDepartment').addEventListener('input', function(e) {
        currentFilters.department = e.target.value.trim();
    });
    
    document.getElementById('userGrade').addEventListener('change', function(e) {
        currentFilters.grade = e.target.value;
    });
    
    // 搜尋按鈕
    document.getElementById('searchBtn').addEventListener('click', searchCourses);
}

// 更新忙碌時間
function updateBusyTimes() {
    busyTimes.clear();
    document.querySelectorAll('.period-checkboxes input[type="checkbox"]:checked').forEach(checkbox => {
        const day = checkbox.dataset.day;
        const period = checkbox.dataset.period;
        busyTimes.add(`${day}-${period}`);
    });
}

// 搜尋課程
function searchCourses() {
    updateBusyTimes();
    
    // 過濾課程：找出時間不衝突的課程
    const matchedCourses = courses.filter(course => {
        return !hasTimeConflict(course.time);
    });
    
    displayResults(matchedCourses);
}

// 檢查課程時間是否衝突
function hasTimeConflict(courseTime) {
    const timeSlots = parseCourseTime(courseTime);
    
    // 只要有任何一個課程時間在忙碌時間內，就算衝突
    return timeSlots.some(slot => busyTimes.has(slot));
}

// 解析課程時間
function parseCourseTime(timeString) {
    const slots = [];
    const parts = timeString.split(',');
    
    parts.forEach(part => {
        const match = part.match(/([一二三四五])([0-9NABCD]+)/);
        if (match) {
            const day = weekdays.indexOf(match[1]) + 1;
            const periods = match[2].split('');
            
            periods.forEach(period => {
                slots.push(`${day}-${period}`);
            });
        }
    });
    
    return slots;
}

// 顯示結果
function displayResults(courses) {
    const tableBody = document.getElementById('courseTableBody');
    const courseCount = document.getElementById('courseCount');
    const resultCount = document.getElementById('resultCount');
    
    courseCount.textContent = courses.length;
    tableBody.innerHTML = '';
    
    if (courses.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="loading-cell">😔 沒有找到符合條件的課程，試著取消一些忙碌時段吧！</td>
            </tr>
        `;
        resultCount.style.display = 'none';
    } else {
        courses.forEach((course, index) => {
            const row = createCourseRow(course, index);
            tableBody.appendChild(row);
        });
        resultCount.style.display = 'block';
    }
}

// 建立課程表格行
function createCourseRow(course, index) {
    const row = document.createElement('tr');
    
    row.innerHTML = `
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
    
    return row;
}

// 格式化時間顯示
function formatTimeDisplay(timeString) {
    // 將 "一234" 轉換為 "週一 2,3,4"
    const parts = timeString.split(',');
    return parts.map(part => {
        const match = part.match(/([一二三四五])([0-9NABCD]+)/);
        if (match) {
            const day = match[1];
            const periods = match[2].split('').join(',');
            return `週${day} ${periods}`;
        }
        return part;
    }).join(' / ');
}
