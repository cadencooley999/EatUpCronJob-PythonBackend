from playwright.sync_api import sync_playwright
import time
import random

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
]

def get_dining_api_response(api_url, max_attempts=5):
    base_url = "https://dineoncampus.com"

    print(f"Attempting to access: {api_url}")
    print(f"Will try up to {max_attempts} attempts")

    for attempt in range(1, max_attempts + 1):
        print(f"\n=== ATTEMPT {attempt}/{max_attempts} ===")
        user_agent = random.choice(USER_AGENTS)
        print(f"Using user agent: {user_agent[:30]}...")

        try:
            with sync_playwright() as p:
                width = random.randint(1024, 1920)
                height = random.randint(768, 1080)

                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    user_agent=user_agent
                )
                page = context.new_page()

                print("Visiting main website...")
                page.goto(base_url)
                time.sleep(random.uniform(1, 3))

                page.evaluate("""
                    window.scrollTo({
                        top: Math.floor(Math.random() * 500),
                        behavior: 'smooth'
                    });
                """)
                time.sleep(random.uniform(0.5, 1.5))

                random_page = random.choice(["/", "/locations", "/hours", "/menus"])
                print(f"Visiting random page: {base_url}{random_page}")
                page.goto(f"{base_url}{random_page}")
                time.sleep(random.uniform(1, 2))

                print("\nFetching API data...")
                response = page.evaluate(f"""async () => {{
                    try {{
                        const cookies = document.cookie;
                        const res = await fetch('{api_url}', {{
                            method: 'GET',
                            headers: {{
                                'Accept': 'application/json, text/plain, */*',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Origin': '{base_url}',
                                'Referer': '{base_url}/',
                                'User-Agent': '{user_agent}',
                                'Cookie': cookies
                            }}
                        }});
                        const json = await res.json();
                        return {{
                            success: res.status === 200,
                            status: res.status,
                            statusText: res.statusText || '',
                            data: json
                        }};
                    }} catch (err) {{
                        return {{
                            success: false,
                            error: err.toString()
                        }};
                    }}
                }}""")

                if 'error' in response:
                    print(f"Error: {response['error']}")
                else:
                    print(f"Status code: {response.get('status', 'unknown')}")
                    if response.get('success'):
                        print("\n✅ SUCCESS! Got a 200 response.")
                        print(f"Response preview: {response.get('responseText', '')[:100]}")
                        return True, response
                    else:
                        print(f"\n❌ Failed with status {response.get('status', 'unknown')}")
                        print(f"Response: {response.get('responseText', '')[:100]}")

                browser.close()
                if attempt < max_attempts:
                    time.sleep(random.uniform(3, 7))

        except Exception as e:
            print(f"Playwright error: {e}")

    print("\n❌ All attempts failed to get a 200 response.")
    return False, None
    
def getWeeklyHours(location, date):

    codes = {'commons' : '5879069fee596f31b3dc146a', 'Harris' : '58790871ee596f31bcdc174d', 'LBJ Marketplace' : '5f4d9a563a585b186379d814'}
    url = f'https://api.dineoncampus.com/v1/locations/weekly_schedule?site_id=576837c0e551b89aabc83157&date={date}T05:00:00.000Z'

    success, response = get_dining_api_response(url)

    if success:
        print("\n=== FINAL RESULT: SUCCESS ===")
        print("Successfully retrieved a 200 response from the API")
    else:
        print("\n=== FINAL RESULT: FAILURE ===")
        print("Failed to get a 200 response after all attempts")

    data = response['data']

    # with open("sampleHoursData.json") as sampleHours:
    #     data = json.load(sampleHours)

    if data:
        allLocations = data["the_locations"]
        selectedLocation = []
        for loc in allLocations:
            if loc["id"] == codes[location]:
                selectedLocation = loc
        week = selectedLocation['week']
        result = []
        for item in week:
            day = item['day']
            if item['closed'] and not item['hours']:
                result.append({
                    'day': day,
                    'hours': '00:00-00:00'
                })
                continue
            if item['closed']:
                continue
            hour_tuples = []
            for hours in item['hours']:
                start_time = (hours['start_hour'], hours['start_minutes'])
                end_time = (hours['end_hour'], hours['end_minutes'])
                hour_tuples.append((start_time, end_time))
            unique_hour_tuples = []
            for hours in hour_tuples:
                if hours not in unique_hour_tuples:
                    unique_hour_tuples.append(hours)
            sorted_hours = sorted(unique_hour_tuples, key=lambda x: (x[0][0], x[0][1]))
            formatted_hours = []
            for (start_hour, start_min), (end_hour, end_min) in sorted_hours:
                start_time = f"{start_hour:02d}:{start_min:02d}"
                end_time = f"{end_hour:02d}:{end_min:02d}"
                formatted_hours.append(f"{start_time}-{end_time}")
            hours_string = ", ".join(formatted_hours)
            result.append({
                'day': day,
                'hours': hours_string
            })      
        return result
    else:
        return ""
     










