"""
Skill: 天气查询
当用户想知道某城市天气时使用此 Skill。支持中文城市名（通过城市→坐标转换）。
数据来源：Open-Meteo（免费无需 Key，https://open-meteo.com/）
城市查询：Open-Meteo Geocoding API
"""

import urllib.parse
import urllib.request
import json

SKILL_NAME        = "🌤️ 天气预报"
SKILL_DESCRIPTION = "查询指定城市的当前天气和未来预报。输入格式：城市名（如：北京、上海）"

# ── WMO 天气码 → 中文描述（Open-Meteo 使用 WMO 标准）─────────
_WMO = {
    0:  "晴天",
    1:  "晴朗",
    2:  "多云",
    3:  "阴天",
    45: "大雾",
    48: "雾凇",
    51: "毛毛雨",
    53: "毛毛雨",
    55: "毛毛雨",
    56: "冻毛毛雨",
    57: "冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨",
    81: "中阵雨",
    82: "大阵雨",
    85: "阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴+冰雹",
    99: "雷暴+大冰雹",
}


def _wmo(code: int) -> str:
    return _WMO.get(code, f"未知({code})")


def _fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _geo(city: str) -> tuple:
    """城市名 → (lat, lon, name)"""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=zh&format=json"
    data = _fetch(url)
    if not data.get("results"):
        raise ValueError(f"未找到城市：{city}")
    r = data["results"][0]
    return r["latitude"], r["longitude"], r.get("name", city)


def run(user_input: str) -> str:
    city = user_input.strip()
    if not city:
        return "[错误] 请提供城市名称，例如：北京"

    try:
        lat, lon, name = _geo(city)
    except Exception as e:
        return f"[错误] 城市查询失败：{e}"

    # ── 天气数据 ────────────────────────────────
    # current=当前 / hourly=逐时 / daily=逐日（已含日出日落）
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,"
        f"is_day,uv_index"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
        f"sunrise,sunset,uv_index_max,precipitation_sum"
        f"&timezone=Asia%2FShanghai&forecast_days=7"
    )
    try:
        data = _fetch(url)
    except Exception as e:
        return f"[错误] 天气数据获取失败：{e}"

    cur  = data["current"]
    daily = data["daily"]

    # 当前
    desc  = _wmo(int(cur["weather_code"]))
    temp  = cur["temperature_2m"]
    feels = cur["apparent_temperature"]
    humid = cur["relative_humidity_2m"]
    wind  = cur["wind_speed_10m"]
    wdir  = _dir(cur["wind_direction_10m"])
    cloud = cur["cloud_cover"]
    uv    = cur.get("uv_index", 0)
    precip = cur["precipitation"]
    is_day = cur["is_day"]

    # 逐日（前7天）
    day_names = []
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    for i, d in enumerate(daily["time"]):
        if d == today:
            day_names.append("今天")
        elif i == 1:
            day_names.append("明天")
        elif i == 2:
            day_names.append("后天")
        else:
            day_names.append(f"{i}天后")

    forecast = []
    for i in range(min(7, len(daily["time"]))):
        d_desc  = _wmo(int(daily["weather_code"][i]))
        d_max   = daily["temperature_2m_max"][i]
        d_min   = daily["temperature_2m_min"][i]
        d_rain  = daily["precipitation_sum"][i]
        d_sunrise = daily["sunrise"][i].split("T")[1] if "T" in daily["sunrise"][i] else daily["sunrise"][i]
        d_sunset  = daily["sunset"][i].split("T")[1] if "T" in daily["sunset"][i] else daily["sunset"][i]
        prefix = "📅" if i == 0 else "  "
        label  = "今日" if i == 0 else day_names[i]
        rain_str = f" 💧{d_rain}mm" if d_rain and float(d_rain) > 0 else ""
        forecast.append(f"{prefix}{label}：{d_desc} {d_min} ~ {d_max}°C 🌅{d_sunrise} 🌇{d_sunset}{rain_str}")

    lines = [
        f"🌍 {name} 天气预报",
        f"",
        f"🌡️  当前：{temp}°C（体感 {feels}°C）{' ☀️' if is_day else ' 🌙'}",
        f"☁️  天气：{desc}",
        f"💧  湿度：{humid}%",
        f"🌬️  风速：{wind} km/h（{wdir}）",
        f"☁️  云量：{cloud}%",
        f"🌧️  降水：{precip} mm",
        f"☀️  UV指数：{uv}",
        "",
        "📅 未来天气预报：",
    ] + forecast

    return "\n".join(lines)


# ── 风向文字 ────────────────────────────────
_DIRS = ["北","北偏东","东北","东偏北","东","东偏南","东南","南偏东",
         "南","南偏西","西南","西偏南","西","西偏北","西北","北偏西"]
def _dir(deg: float) -> str:
    if deg is None:
        return "未知"
    idx = round(deg / 22.5) % 16
    return _DIRS[idx] + f"({deg:.0f}°)"
