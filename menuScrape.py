from openStatusScrape import get_dining_api_response
from MenuItem import MenuItem

#Step 0 - all menu items with tomorrow = true now is false and today is true
#Step 1 - ogurl, get periods
#Step 2 - for each period, get menu except the one we already have 
#Step 3 - for each item in the menus, check if it exists in database
#Step 4 - if it doesn't, add it with tomorrow = true. else set tomorrow = true

#on this file: get all menus and store the items in one huge variable 1-2

locationsMenuCodes = []

Commons = {"LocationCode":"5879069fee596f31b3dc146a", "BreakfastCode":"677d4731e45d4306045bad12", "BrunchCode" : "677d4731e45d4306045bad3b", "LunchCode":"677d4731e45d4306045bad32", "DinnerCode":"677d4731e45d4306045bad22"}
Harris = {"LocationCode":"58790871ee596f31bcdc174d", "BreakfastCode":"66bbea49e45d4307d4cde15a", "BrunchCode" : "", "LunchCode":"66bbea49e45d4307d4cde146", "DinnerCode":"66bbea49e45d4307d4cde154"}
TheDen = {"LocationCode":"66bd0cf4e45d4307d4d6a533", "LunchCode":"66bd0cf4e45d4307d4d6a538"}
nutrientCodes = {'Calories':'682e0cba351d5305de8b5cc9', 'Protein' : '682e0cba351d5305de8b5cca'}

locationsMenuCodes.append(Commons)
locationsMenuCodes.append(Harris)
locationsMenuCodes.append(TheDen)

def getOgUrl(date):
    ogurl = f"https://api.dineoncampus.com/v1/location/5879069fee596f31b3dc146a/periods?platform=0&date={date}"
    return ogurl

def getMenuUrl(perCode, date, locCode='5879069fee596f31b3dc146a'):
    url = f"https://api.dineoncampus.com/v1/location/{locCode}/periods/{perCode}?platform=0&date={date}"
    return url

def getMenuFromPeriod(period, date):
    finalItems = []
    url = getMenuUrl(period, date)
    success, response = get_dining_api_response(url)
    # with open('sampleJsonBreakfast2.json') as f:
    #     BData = json.load(f)
    # response = {}
    # response['data'] = BData
    periodName = response['data']['menu']['periods']['name']
    cats = response['data']['menu']['periods']['categories']
    for cat in cats:
        items = []
        for item in cat['items']:
            calories = next((nut for nut in item["nutrients"] if 'Calories' in nut['name']), None)
            protein = next((nut for nut in item["nutrients"] if 'Protein' in nut['name']), None)
            items.append(
                MenuItem(name=item['name'], calories=calories['value'], protein=protein['value'], today=False, tomorrow=True, category=cat["name"], period=periodName)
            )
        finalItems.extend(items)
    return finalItems

def getFirstMenu(response):
    finalItems = []
    periodName = response['data']['menu']['periods']['name']
    cats = response['data']['menu']['periods']['categories']
    for cat in cats:
        items = []
        for item in cat['items']:
            calories = next((nut for nut in item["nutrients"] if 'Calories' in nut['name']), None)
            protein = next((nut for nut in item["nutrients"] if 'Protein' in nut['name']), None)
            items.append(
                MenuItem(name=item['name'], calories=calories['value'], protein=protein['value'], today=False, tomorrow=True, category=cat["name"], period=periodName)
            )
        finalItems.extend(items)
    return finalItems

def getDailyMenu(date):
    finalItems = []
    success, response = get_dining_api_response(getOgUrl(date))
    finalItems.extend(getFirstMenu(response))
    periods = [per['id'] for per in response['data']['periods']]
    periods.remove(response['data']['menu']['periods']['id'])
    for per in periods:
        finalItems.extend(getMenuFromPeriod(per, date))
    return finalItems
