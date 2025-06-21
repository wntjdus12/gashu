import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()

def get_bus_arrival_info_by_node_id(node_id: str, city_code: str = "33010", num_of_rows: int = 100, page_no: int = 1):
    service_key = unquote(os.getenv("BUS_SERVICE_KEY"))  
    url = "http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList"

    params = {
        'serviceKey': service_key,
        'cityCode': city_code,
        'nodeId': node_id,
        'numOfRows': num_of_rows,
        'pageNo': page_no,
        '_type': 'xml'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except Exception as e:
        print("API 요청 실패:", e)
        return []

    root = ET.fromstring(response.content)
    items = root.findall(".//item")

    results = []
    for item in items:
        arr_time = item.findtext("arrtime")
        if arr_time and arr_time.isdigit():
            seconds = int(arr_time)
            readable_time = "곧 도착" if seconds < 60 else f"{seconds // 60}분 후"
        else:
            readable_time = "도착 정보 없음"

        results.append({
            '노선번호': item.findtext("routeno"),
            '도착예정': readable_time,
            '현재위치': item.findtext("locationno1") or "정보 없음",
            
        })
    return results


if __name__ == "__main__":
    test_node_id = "CJB270000007"
    bus_info = get_bus_arrival_info_by_node_id(test_node_id)
    if bus_info:
        for bus in bus_info:
            print(bus)
    else:
        print("버스 도착 정보를 불러오지 못했습니다.")
