import json
import urllib.request
import csv

def main():
    url = "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
    print("Downloading US cities...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
        lines = [l.decode('utf-8') for l in response.readlines()]
    except Exception as e:
        print(f"Failed to download: {e}")
        return

    reader = csv.DictReader(lines)
    locations = ["United States"]
    # Add states
    states = set()
    cities_by_state = {}
    
    for row in reader:
        state_name = row['STATE_NAME']
        state_code = row['STATE_CODE']
        city = row['CITY']
        states.add((state_name, state_code))
        
        if state_code not in cities_by_state:
            cities_by_state[state_code] = set()
        cities_by_state[state_code].add(city)

    # Sort states
    sorted_states = sorted(list(states), key=lambda x: x[0])
    for s_name, s_code in sorted_states:
        locations.append(f"United States - {s_name}")
        
    # Sort cities
    for s_name, s_code in sorted_states:
        sorted_cities = sorted(list(cities_by_state[s_code]))
        for city in sorted_cities:
            locations.append(f"United States - {city}, {s_code}")

    out_path = r"f:\Vash Studios\FuseHealth\Limitless_marketing_dashboard\static\spa\us_cities.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(locations, f)
        
    print(f"Wrote {len(locations)} locations to {out_path}")

if __name__ == '__main__':
    main()
