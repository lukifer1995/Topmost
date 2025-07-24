import requests

# Từ điển để chuyển mã quốc gia thành tên đầy đủ
COUNTRY_CODES = {
    "SG": "Singapore",
    "US": "United States",
    "VN": "Vietnam",
    "GB": "United Kingdom",
    "IN": "India",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    # ... thêm các quốc gia khác nếu cần
}

def get_ipinfo(ip_port: str, token: str = None) -> str:
    try:
        ip = ip_port.split(':')[0]  # chỉ lấy phần IP
        url = f"https://ipinfo.io/{ip}/json"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return {"ip": ip, "error": f"HTTP {response.status_code}"}

        data = response.json()

        # Chuyển mã quốc gia sang tên đầy đủ nếu có
        country_code = data.get("country", "[!] Unknown")
        try:
            country_full = COUNTRY_CODES.get(country_code, country_code)
        except: country_full = ""
        result = {
            "ip": ip,
            "company": data.get("org", "[!] Unknown"),
            "country": country_full
        }
        result = f"{result['company']} - {result['country']}"
        return result
    except Exception as e:
        return f"ErrorCheckInfoIp: {e}"


if __name__ == '__main__':
    ip_port = "40.99.33.178:443"
    info = get_ipinfo(ip_port)
    print(info)
