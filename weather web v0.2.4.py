"""
天气查询小助手 - Flask 网页版
数据来源：腾讯天气公开API（免费，无需Key）
"""

import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string

# ======================== 城市数据加载 ========================
CITY_MAP = {}
BASE_DIR = os.path.dirname(__file__)
json_path = os.path.join(BASE_DIR, "city_data.json")
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_map = data.get("city_map", {})
    CITY_MAP = {city: (prov, city) for city, prov in raw_map.items()}

# 临沂三区九县
for county in ["兰山", "罗庄", "河东", "沂南", "郯城", "沂水",
               "兰陵", "费县", "平邑", "莒南", "蒙阴", "临沭"]:
    if county not in CITY_MAP:
        CITY_MAP[county] = ("山东", "临沂")

# 省份映射
PROVINCE_MAP = {
    "广东": "广州", "山东": "济南", "浙江": "杭州", "江苏": "南京",
    "福建": "福州", "江西": "南昌", "湖南": "长沙", "湖北": "武汉",
    "河南": "郑州", "河北": "石家庄", "山西": "太原", "陕西": "西安",
    "甘肃": "兰州", "青海": "西宁", "四川": "成都", "贵州": "贵阳",
    "云南": "昆明", "辽宁": "沈阳", "吉林": "长春", "黑龙江": "哈尔滨",
    "安徽": "合肥", "广西": "南宁", "海南": "海口",
    "内蒙古": "呼和浩特", "新疆": "乌鲁木齐", "西藏": "拉萨", "宁夏": "银川",
    "台湾": "台北",
}
for prov, capital in PROVINCE_MAP.items():
    if prov not in CITY_MAP:
        CITY_MAP[prov] = (prov, capital)

print(f"🌍 已加载 {len(CITY_MAP)} 个城市数据")


# ======================== API 调用 ========================
def get_weather(city_name):
    if city_name not in CITY_MAP:
        return None, f"暂不支持「{city_name}」"

    province, city = CITY_MAP[city_name]
    url = "https://wis.qq.com/weather/common"
    params = {
        "source": "xw",
        "weather_type": "observe|forecast_1h|forecast_24h|alarm",
        "province": province,
        "city": city,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.encoding = "utf-8"
        data = resp.json()
        if data.get("status") != 200:
            return None, f"API错误：{data.get('message', '')}"
        return data, None
    except Exception as e:
        return None, f"请求失败：{str(e)}"


# ======================== Flask 应用 ========================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>天气查询小助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #e8f4f8 0%, #d4edf5 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 30px 15px;
        }
        .container {
            max-width: 520px;
            width: 100%;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            padding: 25px;
            margin-bottom: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            color: #1565C0;
            font-size: 24px;
            margin-bottom: 15px;
        }
        .search-box {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        .search-box input {
            flex: 1;
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-box input:focus { border-color: #2196F3; }
        .search-box button {
            padding: 10px 18px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s;
            white-space: nowrap;
        }
        .search-box button:hover { background: #1976D2; }
        .search-box button:disabled { background: #ccc; cursor: wait; }

        .fav-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
            min-height: 32px;
            margin-bottom: 10px;
        }
        .fav-bar .fav-title { font-size: 14px; color: #E65100; margin-right: 4px; }
        .fav-bar .fav-btn {
            padding: 4px 12px;
            background: #FFF3E0;
            color: #E65100;
            border: 1px solid #FFCC80;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .fav-bar .fav-btn:hover { background: #FFE0B2; }
        .fav-bar .fav-empty { font-size: 13px; color: #aaa; }

        .toggle-fav {
            text-align: center;
            margin-bottom: 12px;
        }
        .toggle-fav button {
            padding: 6px 20px;
            border: none;
            border-radius: 20px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .toggle-fav .fav-off { background: #E0E0E0; color: #555; }
        .toggle-fav .fav-on { background: #FFA726; color: white; }

        .result {
            line-height: 1.8;
            font-size: 15px;
            color: #333;
        }
        .result .city-title {
            font-size: 18px;
            font-weight: bold;
            color: #1565C0;
            margin-bottom: 8px;
        }
        .result .divider {
            border: none;
            border-top: 2px dashed #ddd;
            margin: 12px 0;
        }
        .result .weather-main {
            font-size: 28px;
            text-align: center;
            margin: 10px 0;
        }
        .result .weather-main .icon { font-size: 36px; }
        .result .weather-main .temp { font-size: 40px; font-weight: bold; color: #E65100; }
        .result .info-row { padding: 3px 0; }
        .fc-scroll-wrap {
            overflow-x: auto;
            white-space: nowrap;
            padding: 5px 0 10px 0;
            scrollbar-width: thin;
            cursor: grab;
            user-select: none;
            -webkit-overflow-scrolling: touch;
        }
        .fc-scroll-wrap::-webkit-scrollbar { height: 4px; }
        .fc-scroll-wrap::-webkit-scrollbar-track { background: #e0e0e0; border-radius: 2px; }
        .fc-scroll-wrap::-webkit-scrollbar-thumb { background: #90CAF9; border-radius: 2px; }
        .result .forecast-day {
            background: #f5f5f5;
            border-radius: 12px;
            padding: 10px 14px;
            margin: 0 5px;
            display: inline-block;
            vertical-align: top;
            white-space: normal;
            width: 110px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .result .forecast-day:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .result .forecast-day .day-name { font-weight: bold; color: #1565C0; font-size: 13px; display: block; margin-bottom: 4px; }
        .result .forecast-day .day-icon { font-size: 22px; display: block; margin: 4px 0; }
        .result .forecast-day .day-temp { font-size: 14px; }
        .result .forecast-day .day-temp .hi { color: #E65100; font-weight: bold; }
        .result .forecast-day .day-temp .lo { color: #1565C0; }
        .loading {
            text-align: center;
            color: #888;
            font-size: 16px;
            padding: 30px 0;
        }
        .error {
            text-align: center;
            color: #D32F2F;
            font-size: 16px;
            padding: 20px 0;
        }
        .welcome {
            text-align: center;
            color: #555;
            padding: 10px 0;
            line-height: 2;
        }
        .welcome h2 { color: #1565C0; margin-bottom: 10px; }
        .footer {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
        }
        .alert-box {
            background: #FFF3E0;
            border: 2px solid #FF9800;
            border-radius: 10px;
            padding: 12px 15px;
            margin-bottom: 12px;
        }
        .alert-box.red { background: #FFEBEE; border-color: #F44336; }
        .alert-box.orange { background: #FFF3E0; border-color: #FF9800; }
        .alert-box.yellow { background: #FFFDE7; border-color: #FFC107; }
        .alert-item { margin: 4px 0; font-size: 14px; }
        .alert-item .icon { font-size: 18px; margin-right: 6px; }
        .alert-item .title { font-weight: bold; }
        .alert-item .detail { font-size: 13px; color: #666; margin-top: 2px; }
        .chart-wrap {
            background: #fafafa;
            border-radius: 10px;
            padding: 10px;
            margin: 10px 0;
            text-align: center;
        }
        .chart-wrap canvas { width: 100%; height: 140px; }
        .chart-title { font-weight: bold; color: #1565C0; margin-bottom: 6px; font-size: 14px; }
        @media (max-width: 480px) {
            .card { padding: 18px; }
            h1 { font-size: 20px; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>☀️ 天气查询小助手</h1>
        <div class="search-box">
            <input type="text" id="cityInput" placeholder="输入城市或省份（如：北京、广东、临沂）"
                   onkeydown="if(event.key==='Enter') search()">
            <button id="searchBtn" onclick="search()">🔍 查天气</button>
        </div>

        <div class="toggle-fav">
            <button id="favBtn" class="fav-off" onclick="toggleFav()" disabled>☆ 收藏</button>
        </div>

        <div class="fav-bar" id="favBar"></div>

        <hr class="divider">

        <div id="resultArea" class="result">
            <div class="welcome">
                <h2>🌤 天气查询小助手</h2>
                <p>在上方输入城市名，按回车查询</p>
                <p>支持全国 340+ 个地级市</p>
                <p>查天气后可收藏城市快速查看</p>
                <p style="color:#aaa;margin-top:8px;">示例：北京 · 广东 · 临沂 · 兰山</p>
            </div>
        </div>
    </div>
    <div class="footer">数据来源：腾讯天气 API · 无需注册免费使用</div>
</div>

<script>
    // ========== 收藏功能 ==========
    let currentCity = null;
    let favorites = JSON.parse(localStorage.getItem('weather_fav') || '[]');

    function saveFavs() {
        localStorage.setItem('weather_fav', JSON.stringify(favorites));
        renderFavBar();
    }

    function renderFavBar() {
        const bar = document.getElementById('favBar');
        if (favorites.length === 0) {
            bar.innerHTML = '<span class="fav-empty">❤️ 收藏栏为空，查天气后点击 ☆收藏 添加</span>';
            return;
        }
        let html = '<span class="fav-title">❤️</span>';
        favorites.forEach(c => {
            html += `<button class="fav-btn" onclick="quickSearch('${c}')">${c}</button>`;
        });
        bar.innerHTML = html;
    }

    function quickSearch(city) {
        document.getElementById('cityInput').value = city;
        search();
    }

    function toggleFav() {
        if (!currentCity) return;
        const idx = favorites.indexOf(currentCity);
        const btn = document.getElementById('favBtn');
        if (idx >= 0) {
            favorites.splice(idx, 1);
            btn.textContent = '☆ 收藏';
            btn.className = 'fav-off';
        } else {
            favorites.push(currentCity);
            btn.textContent = '★ 已收藏';
            btn.className = 'fav-on';
        }
        saveFavs();
    }

    function updateFavBtn(city) {
        const btn = document.getElementById('favBtn');
        currentCity = city;
        if (favorites.includes(city)) {
            btn.textContent = '★ 已收藏';
            btn.className = 'fav-on';
        } else {
            btn.textContent = '☆ 收藏';
            btn.className = 'fav-off';
        }
        btn.disabled = false;
    }

    // ========== 天气查询 ==========
    function search() {
        const city = document.getElementById('cityInput').value.trim();
        if (!city) { alert('请输入城市名称'); return; }

        const area = document.getElementById('resultArea');
        area.innerHTML = '<div class="loading">⏳ 正在查询 ' + city + ' 的天气...</div>';

        const btn = document.getElementById('searchBtn');
        btn.disabled = true;

        fetch('/api/weather?city=' + encodeURIComponent(city))
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    area.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                    return;
                }
                renderWeather(data);
                updateFavBtn(city);
            })
            .catch(err => {
                area.innerHTML = '<div class="error">❌ 网络错误，请重试</div>';
            })
            .finally(() => { btn.disabled = false; });
    }

    function renderWeather(data) {
        const o = data.observe;
        const fc = data.forecast || {};
        const alerts = data.alerts || [];

        const iconMap = {
            "晴":"☀️","多云":"⛅","阴":"☁️","小雨":"🌦️","中雨":"🌧️",
            "大雨":"🌧️","暴雨":"🌊","雷阵雨":"⛈️","小雪":"🌨️","中雪":"❄️",
            "大雪":"❄️","雾":"🌫️","霾":"😷"
        };
        const icon = iconMap[o.weather] || "🌤️";

        // 预警
        let alertHtml = '';
        if (alerts.length > 0) {
            let levelClass = 'yellow';
            const levels = alerts.map(a => a.level);
            if (levels.includes('红色')) levelClass = 'red';
            else if (levels.includes('橙色')) levelClass = 'orange';

            alertHtml = '<div class="alert-box ' + levelClass + '">';
            alerts.forEach(a => {
                alertHtml += '<div class="alert-item">' +
                    '<span class="icon">' + a.icon + '</span>' +
                    '<span class="title">' + a.title + '</span>' +
                    '<div class="detail">' + a.detail + '</div>' +
                    '</div>';
            });
            alertHtml += '</div>';
        }

        // 预报（横向滑动卡片）
        let fcHtml = '<div class="fc-scroll-wrap" id="fcScroll">';
        for (let i = 0; i < 7; i++) {
            const d = fc[i];
            if (!d) continue;
            const di = iconMap[d.day_weather] || "🌤️";
            fcHtml += '<div class="forecast-day">' +
                '<span class="day-name">' + d.date.split(' ')[1] + '</span>' +
                '<span class="day-icon">' + di + '</span>' +
                '<span class="day-temp"><span class="hi">' + d.max_deg + '°</span> <span class="lo">' + d.min_deg + '°</span></span>' +
                '<div style="font-size:11px;color:#888;margin-top:2px;">' + d.day_weather + '</div>' +
                '</div>';
        }
        fcHtml += '</div>';


        const html = `
            ${alertHtml}
            <div class="city-title">📍 ${data.display_name}  当前天气</div>
            <hr class="divider">
            <div class="weather-main">
                <div class="icon">${icon}</div>
                <div class="temp">${o.degree}°C</div>
                <div>${o.weather}</div>
            </div>
            <hr class="divider">
            <div class="info-row">💧 湿度：${o.humidity}%</div>
            <div class="info-row">🌬️ 风向：${o.wind_dir} ${o.wind_power}级</div>
            <div class="info-row">🌀 气压：${o.pressure}hPa</div>
            <div class="info-row">🕐 更新：${o.update_time}</div>
            <hr class="divider">
            <div class="chart-wrap">
                <div class="chart-title">📈 未来24小时温度变化</div>
                <canvas id="tempChart" width="460" height="140"></canvas>
            </div>
            <hr class="divider">
            <div style="font-weight:bold;color:#1565C0;">📅 未来七天预报</div>
            ${fcHtml}
        `;
        document.getElementById('resultArea').innerHTML = html;

        // 画折线图
        if (data.hourly && data.hourly.length > 0) {
            drawTempChart(data.hourly);
        }


    }

    function drawTempChart(hourly) {
        const canvas = document.getElementById('tempChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;

        // 取温度数据
        const temps = hourly.map(h => parseFloat(h.degree) || 0);
        const labels = hourly.map(h => h.hour);

        // 每隔3小时显示一个标签
        const step = 3;
        const maxT = Math.max(...temps);
        const minT = Math.min(...temps);
        const range = Math.max(maxT - minT, 5);
        const padTop = 20, padBottom = 20, padLeft = 30, padRight = 15;
        const chartW = w - padLeft - padRight;
        const chartH = h - padTop - padBottom;

        function xPos(i) { return padLeft + (i / (temps.length - 1)) * chartW; }
        function yPos(v) { return padTop + chartH - ((v - minT + 2) / (range + 4)) * chartH; }

        ctx.clearRect(0, 0, w, h);

        // 背景网格
        ctx.strokeStyle = "#e8e8e8";
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padTop + (i / 4) * chartH;
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(w - padRight, y);
            ctx.stroke();
            // 温度标签
            const tempVal = Math.round(minT + (4 - i) * (range + 4) / 4);
            ctx.fillStyle = "#999";
            ctx.font = "10px sans-serif";
            ctx.textAlign = "right";
            ctx.fillText(tempVal + "°", padLeft - 4, y + 4);
        }

        // 折线
        ctx.beginPath();
        ctx.strokeStyle = "#2196F3";
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        temps.forEach((t, i) => {
            const x = xPos(i), y = yPos(t);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.stroke();

        // 填充渐变
        ctx.lineTo(xPos(temps.length - 1), h - padBottom);
        ctx.lineTo(xPos(0), h - padBottom);
        ctx.closePath();
        const grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
        grad.addColorStop(0, "rgba(33,150,243,0.2)");
        grad.addColorStop(1, "rgba(33,150,243,0.02)");
        ctx.fillStyle = grad;
        ctx.fill();

        // 数据点 + 温度值
        ctx.fillStyle = "#1565C0";
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";

        // 只显示关键点（每3小时一个）
        temps.forEach((t, i) => {
            const x = xPos(i), y = yPos(t);
            if (i % step === 0 || i === temps.length - 1) {
                // 圆点
                ctx.beginPath();
                ctx.arc(x, y, 3.5, 0, Math.PI * 2);
                ctx.fillStyle = "#1565C0";
                ctx.fill();
                ctx.strokeStyle = "#fff";
                ctx.lineWidth = 1.5;
                ctx.stroke();
                // 温度
                ctx.fillStyle = "#1565C0";
                ctx.fillText(t + "°", x, y - 10);
                // 时间标签
                ctx.fillStyle = "#999";
                ctx.font = "10px sans-serif";
                ctx.fillText(labels[i], x, h - 5);
            }
        });
    }

    // 初始化
    renderFavBar();
</script>
</body>
</html>
"""


# ======================== Flask 路由 ========================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "请输入城市名称"})

    # 判断显示名称
    linyi_cities = ["兰山", "罗庄", "河东", "沂南", "郯城", "沂水",
                    "兰陵", "费县", "平邑", "莒南", "蒙阴", "临沭"]
    display = city
    if city in linyi_cities:
        display = f"{city}（临沂）"
    elif city in PROVINCE_MAP:
        display = f"{city}（省会：{PROVINCE_MAP[city]}）"

    data, error = get_weather(city)
    if error:
        return jsonify({"error": error})

    observe = data.get("data", {}).get("observe", {})
    forecast = data.get("data", {}).get("forecast_24h", {})

    if not observe:
        return jsonify({"error": "未获取到天气数据"})

    # 格式化更新时间
    update_time = observe.get("update_time", "")
    if len(update_time) >= 10:
        try:
            from datetime import datetime
            dt = datetime.strptime(update_time, "%Y%m%d%H%M")
            update_time = dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass

    # 整理预报数据
    fc_list = []
    for i in range(7):
        day = forecast.get(str(i))
        if day:
            day_date = day.get("time", "")
            if day_date:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(day_date, "%Y-%m-%d")
                    wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]
                    day_date = f"{dt.month}月{dt.day}日 {wd}"
                except:
                    pass
            fc_list.append({
                "date": day_date,
                "day_weather": day.get("day_weather", "?"),
                "night_weather": day.get("night_weather", "?"),
                "max_deg": day.get("max_degree", "?"),
                "min_deg": day.get("min_degree", "?"),
            })

    # ===== 逐小时温度数据（未来24小时） =====
    hourly_data = data.get("data", {}).get("forecast_1h", {})
    hourly_list = []
    # 取接下来24小时的数据
    sorted_keys = sorted(hourly_data.keys(), key=lambda x: int(x))
    for idx in sorted_keys[:24]:
        h = hourly_data[idx]
        try:
            ts = h.get("update_time", "")
            hour = ts[8:10] + ":00" if len(ts) >= 10 else "?"
        except:
            hour = "?"
        hourly_list.append({
            "hour": hour,
            "degree": h.get("degree", "?"),
            "weather": h.get("weather", ""),
        })

    # ===== 预警处理 =====
    alerts = []

    # 1. 官方预警
    alarm_data = data.get("data", {}).get("alarm", [])
    for alarm in alarm_data:
        alerts.append({
            "type": "official",
            "level": alarm.get("level_name", "未知"),
            "title": f"{alarm.get('type_name', '')}{alarm.get('level_name', '')}预警",
            "detail": alarm.get("detail", ""),
            "icon": "🔴" if alarm.get("level_name") == "红色" else "🟠" if alarm.get("level_name") == "橙色" else "🟡",
        })

    # 2. 预报分析预警（当没有官方预警时补充）
    if not alarm_data:
        for i in range(3):
            day = forecast.get(str(i))
            if day:
                dw = day.get("day_weather", "")
                nw = day.get("night_weather", "")
                dp = day.get("day_wind_power", "")
                np = day.get("night_wind_power", "")

                if "暴雨" in dw or "暴雨" in nw:
                    alerts.append({"type": "forecast", "level": "橙色", "title": "⚠️ 暴雨预警", "detail": "未来24小时可能出现暴雨天气，请注意防范", "icon": "🟠"})
                elif "大雨" in dw or "大雨" in nw:
                    alerts.append({"type": "forecast", "level": "黄色", "title": "🌧️ 大雨提醒", "detail": "预计有中到大雨，出门请带伞", "icon": "🟡"})
                if "雷阵雨" in dw or "雷阵雨" in nw:
                    alerts.append({"type": "forecast", "level": "黄色", "title": "⛈️ 雷阵雨提醒", "detail": "预计有雷阵雨，请注意防雷避险", "icon": "🟡"})
                if any(x in dp for x in ["5","6","7","8","9"]) or any(x in np for x in ["5","6","7","8","9"]):
                    alerts.append({"type": "forecast", "level": "黄色", "title": "💨 大风提醒", "detail": "风力较大(5级以上)，请注意防风", "icon": "🟡"})

    return jsonify({
        "display_name": display,
        "observe": {
            "degree": observe.get("degree", "?"),
            "weather": observe.get("weather", "?"),
            "humidity": observe.get("humidity", "?"),
            "wind_dir": observe.get("wind_direction_name", "?"),
            "wind_power": observe.get("wind_power", "?"),
            "pressure": observe.get("pressure", "?"),
            "update_time": update_time,
        },
        "forecast": fc_list,
        "hourly": hourly_list,
        "alerts": alerts,
    })


# ======================== 启动 ========================
if __name__ == "__main__":
    import socket
    from werkzeug.serving import BaseWSGIServer, WSGIRequestHandler

    # 创建支持 IPv4+IPv6 双栈的服务器
    class DualStackServer(BaseWSGIServer):
        address_family = socket.AF_INET6

        def server_bind(self):
            self.socket = socket.socket(self.address_family, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except (AttributeError, OSError):
                pass
            self.socket.bind(self.server_address)
            self.socket.listen(self.request_queue_size)

    server = DualStackServer("::", 5000, app, WSGIRequestHandler)

    print("🚀 天气查询小助手 - 网页版已启动！")
    print(f"  本机IPv4: http://127.0.0.1:5000")
    print(f"  本机IPv6: http://[::1]:5000")
    print(f"  局域网IPv4: http://<你的IPv4地址>:5000")
    print(f"  IPv6: http://[<你的IPv6地址>]:5000")
    print("  按 Ctrl+C 停止服务\n")

    server.serve_forever()