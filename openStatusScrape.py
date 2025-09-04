# from playwright.sync_api import sync_playwright
# import json
# import time
# import random

# # User agents for rotation
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
# ]

# def get_dining_api_response(api_url, max_attempts=5):
#     base_url = "https://apiv4.dineoncampus.com"

#     print(f"Attempting to access: {api_url}")
#     print(f"Will try up to {max_attempts} attempts")

#     for attempt in range(1, max_attempts + 1):
#         print(f"\n=== ATTEMPT {attempt}/{max_attempts} ===")
#         user_agent = random.choice(USER_AGENTS)
#         print(f"Using user agent: {user_agent[:30]}...")

#         try:
#             with sync_playwright() as p:
#                 width = random.randint(1024, 1920)
#                 height = random.randint(768, 1080)

#                 browser = p.chromium.launch(headless=True)
#                 context = browser.new_context(
#                     viewport={"width": width, "height": height},
#                     user_agent=user_agent
#                 )
#                 page = context.new_page()

#                 print("Visiting main website...")
#                 page.goto('https://new.dineoncampus.com')
#                 time.sleep(random.uniform(1, 3))

#                 page.evaluate("""
#                     window.scrollTo({
#                         top: Math.floor(Math.random() * 500),
#                         behavior: 'smooth'
#                     });
#                 """)
#                 time.sleep(random.uniform(0.5, 1.5))

#                 random_page = random.choice(["/", "/locations", "/hours", "/menus"])
#                 print(f"Visiting random page: {base_url}{random_page}")
#                 page.goto(f"{base_url}{random_page}")
#                 time.sleep(random.uniform(1, 2))

#                 print("\nFetching API data...")
#                 response = page.evaluate(f"""async () => {{
#                     try {{
#                         const cookies = document.cookie;
#                         const res = await fetch('{api_url}', {{
#                             method: 'GET',
#                             headers: {{
#                                 'Accept': 'application/json, text/plain, */*',
#                                 'Accept-Language': 'en-US,en;q=0.9',
#                                 'Origin': '{base_url}',
#                                 'Referer': '{base_url}/',
#                                 'User-Agent': '{user_agent}',
#                                 'Cookie': cookies
#                             }}
#                         }});
#                         const json = await res.json();
#                         return {{
#                             success: res.status === 200,
#                             status: res.status,
#                             statusText: res.statusText || '',
#                             data: json
#                         }};
#                     }} catch (err) {{
#                         return {{
#                             success: false,
#                             error: err.toString()
#                         }};
#                     }}
#                 }}""")

#                 if 'error' in response:
#                     print(f"Error: {response['error']}")
#                 else:
#                     print(f"Status code: {response.get('status', 'unknown')}")
#                     if response.get('success'):
#                         print("\n✅ SUCCESS! Got a 200 response.")
#                         print(f"Response preview: {response.get('responseText', '')[:100]}")
#                         return True, response
#                     else:
#                         print(f"\n❌ Failed with status {response.get('status', 'unknown')}")
#                         print(f"Response: {response.get('responseText', '')[:100]}")

#                 browser.close()
#                 if attempt < max_attempts:
#                     time.sleep(random.uniform(3, 7))

#         except Exception as e:
#             print(f"Playwright error: {e}")

#     print("\n❌ All attempts failed to get a 200 response.")
#     return False, None
    
# def getWeeklyHours(location, date):

#     codes = {'Commons' : '5879069fee596f31b3dc146a', 'Harris' : '58790871ee596f31bcdc174d', 'LBJ Marketplace' : '5f4d9a563a585b186379d814'}
#     url = f'https://apiv4.dineoncampus.com/locations/weekly_schedule?site_id=576837c0e551b89aabc83157&date={date}'

#     success, response = get_dining_api_response(url)

#     if success:
#         print("\n=== FINAL RESULT: SUCCESS ===")
#         print("Successfully retrieved a 200 response from the API")
#     else:
#         print("\n=== FINAL RESULT: FAILURE ===")
#         print("Failed to get a 200 response after all attempts")

#     data = response['data']

#     # with open("sampleHoursData.json") as sampleHours:
#     #     data = json.load(sampleHours)

#     if data:
#         allLocations = data["theLocations"]
#         selectedLocation = []
#         for loc in allLocations:
#             if loc["id"] == codes[location]:
#                 selectedLocation = loc
#         week = selectedLocation['week']
#         result = []
#         for item in week:
#             day = item['day']
#             if item['closed'] and not item['hours']:
#                 result.append({
#                     'day': day,
#                     'hours': '00:00-00:00'
#                 })
#                 continue
#             if item['closed']:
#                 continue
#             hour_tuples = []
#             for hours in item['hours']:
#                 start_time = (hours['start_hour'], hours['start_minutes'])
#                 end_time = (hours['end_hour'], hours['end_minutes'])
#                 hour_tuples.append((start_time, end_time))
#             unique_hour_tuples = []
#             for hours in hour_tuples:
#                 if hours not in unique_hour_tuples:
#                     unique_hour_tuples.append(hours)
#             sorted_hours = sorted(unique_hour_tuples, key=lambda x: (x[0][0], x[0][1]))
#             formatted_hours = []
#             for (start_hour, start_min), (end_hour, end_min) in sorted_hours:
#                 start_time = f"{start_hour:02d}:{start_min:02d}"
#                 end_time = f"{end_hour:02d}:{end_min:02d}"
#                 formatted_hours.append(f"{start_time}-{end_time}")
#             hours_string = ", ".join(formatted_hours)
#             result.append({
#                 'day': day,
#                 'hours': hours_string
#             })      
#         return result
#     else:
#         return ""
     
import httpx
import random
import time

USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36 Edg/116.0.1938.81",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36",
    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Mobile Safari/537.36",
    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Firefox on Android
    "Mozilla/5.0 (Android 13; Mobile; rv:117.0) Gecko/117.0 Firefox/117.0",
    # Edge on Android
    "Mozilla/5.0 (Linux; Android 13; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Mobile Safari/537.36 EdgA/116.0.1938.81"
]

def get_dining_api_response(api_url: str, max_attempts: int = 5, timeout: int = 20):
    """
    Fetch JSON from DineOnCampus API with retries.
    Returns (success: bool, response: dict | None)
    """
    base_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://new.dineoncampus.com/",
        "Origin": "https://new.dineoncampus.com",
        "Connection": "keep-alive"
    }

    http2_enabled = True

    print("attempting to fetch: ", api_url)

    for attempt in range(1, max_attempts + 1):
        headers = base_headers.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)

        try:
            with httpx.Client(timeout=timeout, http2=http2_enabled, follow_redirects=True) as client:
                resp = client.get(api_url, headers=headers)

            if resp.status_code == 200:
                try:
                    return True, resp.json()
                except ValueError:
                    print(f"❌ Attempt {attempt}: Invalid JSON response")
                    return False, None

            # Server responded but not 200
            print(f"❌ Attempt {attempt}: HTTP {resp.status_code} - {resp.text[:100]}")

            # Optional: if 422 or other throttling, consider switching HTTP/2 off
            if resp.status_code in {422, 429, 503}:
                http2_enabled = False

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            print(f"⚠️ Attempt {attempt} failed: {e}")
            # If a connection reset happens, try disabling HTTP/2 next time
            if "ConnectionResetError" in str(e) or "104" in str(e):
                http2_enabled = False

        # Exponential backoff with jitter
        sleep_time = min(10, 2 ** attempt + random.random())
        time.sleep(sleep_time)

    return False, None

def getWeeklyHours(location, date):

    codes = {'Commons' : '5879069fee596f31b3dc146a', 'Harris' : '58790871ee596f31bcdc174d', 'LBJ Marketplace' : '5f4d9a563a585b186379d814'}
    url = f'https://apiv4.dineoncampus.com/locations/weekly_schedule?site_id=576837c0e551b89aabc83157&date={date}'

    success, response = get_dining_api_response(url)

    if success:
        print("\n=== FINAL RESULT: SUCCESS ===")
        print("Successfully retrieved a 200 response from the API")
    else:
        print("\n=== FINAL RESULT: FAILURE ===")
        print("Failed to get a 200 response after all attempts")

    data = response

    # with open("sampleHoursData.json") as sampleHours:
    #     data = json.load(sampleHours)

    if data:
        allLocations = data["theLocations"]
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









