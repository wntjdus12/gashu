import pandas as pd
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict

station_file = "bus_station.csv"  
interval_file = "interval.csv"     


def calculate_distance(lat1, lon1, lat2, lon2):
    return ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5


def get_bus_arrival_info(node_id, city_code="33010"):
    service_key = "bAlGo8KFB+yRHKW7ETRFeJVvF2FNosTVyTLtMDXTbDbbmdql21rAg3x6Ly4CV1pcZTDuHqJlpUwjxy3oUqRZRQ=="
    url = "http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList"
    params = {
        "serviceKey": service_key,
        "cityCode": city_code,
        "nodeId": node_id,
        "numOfRows": 10,
        "pageNo": 1,
        "_type": "xml"
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ API 요청 오류: {e}")
        return []

    root = ET.fromstring(res.content)
    items = root.findall(".//item")

    results = []
    for item in items:
        arrtime = item.findtext("arrtime")
        if arrtime and arrtime.isdigit():
            seconds = int(arrtime)
            if seconds < 60:
                time_text = "곧 도착"
            else:
                minutes = seconds // 60
                time_text = f"{minutes}분 후"
            results.append({
                "노선번호": item.findtext("routeno"),
                "도착시간_초": seconds,
                "도착시간": time_text
            })
    return results


def show_bus_info_with_interval(my_lat, my_lon):
    station_df = pd.read_csv(station_file)
    interval_df = pd.read_csv(interval_file)

   
    station_df['distance'] = station_df.apply(
        lambda row: calculate_distance(my_lat, my_lon, row['gpslati'], row['gpslong']), axis=1)
    nearest = station_df.loc[station_df['distance'].idxmin()]

    print(f"\n📍 가장 가까운 정류소: {nearest['nodenm']} ({nearest['nodeid']})\n")

    
    interval_map = interval_df.set_index('routeno')['intervaltime'].dropna().astype(int).to_dict()

    buses = get_bus_arrival_info(nearest['nodeid'])
    if not buses:
        print(" 현재 운행 중인 버스 없음")
        return

    grouped = defaultdict(list)
    for r in buses:
        grouped[r["노선번호"]].append(r)

    for route, route_buses in grouped.items():
        sorted_buses = sorted(route_buses, key=lambda x: x["도착시간_초"])
        for i, b in enumerate(sorted_buses):
            line = f"🚌 {route}번 - {b['도착시간']}"
            if i < len(sorted_buses) - 1:
                diff = (sorted_buses[i+1]["도착시간_초"] - b["도착시간_초"]) // 60
                line += f" ({diff}분 간격)"
            if i == 0 and route in interval_map:
                line += f" / 배차간격: {interval_map[route]}분"
            print(line)


if __name__ == "__main__":
    # 청주 모충사거리 부근
    show_bus_info_with_interval(36.6200, 127.4600)
