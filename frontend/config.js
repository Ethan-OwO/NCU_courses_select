// API 配置
const API_CONFIG = {
    // 本地開發環境
    development: 'http://localhost:3000',
    // 生產環境 - 部署後改成你的 Render URL
    production: 'https://ncu-courses-select.onrender.com'
};

// 自動偵測環境
const API_BASE_URL = window.location.hostname === 'localhost'
    ? API_CONFIG.development
    : API_CONFIG.production;
