from playwright.sync_api import sync_playwright
import json

def get_dining_api_response(api_url):
    """
    Fetch JSON from a DineOnCampus API URL using Playwright.
    Returns: (True, data) on success, (False, None) on failure.
    """
    ROOT = "https://new.dineoncampus.com/"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Visit root once to solve Cloudflare
            page.goto(ROOT, wait_until="networkidle", timeout=60000)

            # Fetch API URL inside the browser context
            js = f"""
                () => fetch("{api_url}", {{
                    method: "GET",
                    headers: {{
                        "accept": "application/json, text/plain, */*"
                    }}
                }}).then(r => r.text())
            """
            body = page.evaluate(js)

            # Parse JSON
            try:
                data = json.loads(body)
                return True, data
            except Exception:
                print(f"[!] Failed to parse JSON for {url}")
                print("Body (first 300 chars):", body[:300])
                return False, None

    except Exception as e:
        print(f"[!] Exception fetching {api_url}: {e}")
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
    
from playwright.sync_api import sync_playwright
import json

def fetch_multiple_dining_json(urls):
    """
    Fetch JSON from multiple DineOnCampus API URLs in a single browser session.
    Input: list of URLs
    Output: dict of {url: (True, data) or (False, None)}
    """
    ROOT = "https://new.dineoncampus.com/"
    results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Visit root once to solve Cloudflare
            page.goto(ROOT, wait_until="networkidle", timeout=60000)

            for url in urls:
                try:
                    js = f"""
                        () => fetch("{url}", {{
                            method: "GET",
                            headers: {{
                                "accept": "application/json, text/plain, */*"
                            }}
                        }}).then(r => r.text())
                    """
                    body = page.evaluate(js)

                    try:
                        data = json.loads(body)
                        results[url] = (True, data)
                    except Exception:
                        print(f"[!] Failed to parse JSON for {url}")
                        print("Body (first 300 chars):", body[:300])
                        results[url] = (False, None)

                except Exception as e:
                    print(f"[!] Exception fetching {url}: {e}")
                    results[url] = (False, None)

            return True, results

    except Exception as e:
        print(f"[!] Top-level exception: {e}")
        return False, None

    finally:
        try:
            browser.close()
        except:
            pass