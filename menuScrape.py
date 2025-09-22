import firebase_admin
from firebase_admin import firestore, credentials, messaging
import re
from newOpenStatusScrape import get_dining_api_response, fetch_multiple_dining_json
from MenuItem import MenuItem
from datetime import datetime
import time
import random

#Step 0 - all menu items with tomorrow = true now is false and today is true
#Step 1 - ogurl, get periods
#Step 2 - for each period, get menu except the one we already have 
#Step 3 - for each item in the menus, check if it exists in database
#Step 4 - if it doesn't, add it with tomorrow = true. else set tomorrow = true

#on this file: get all menus and store the items in one huge variable 1-2

locationsMenuCodes = []

Commons = {"LocationCode":"5879069fee596f31b3dc146a", "BreakfastCode":"677d4731e45d4306045bad12", "BrunchCode" : "677d4731e45d4306045bad3b", "LunchCode":"677d4731e45d4306045bad32", "DinnerCode":"677d4731e45d4306045bad22"}
Harris = {"LocationCode":"58790871ee596f31bcdc174d", "BreakfastCode":"66bbea49e45d4307d4cde15a", "BrunchCode" : "", "LunchCode":"68a0c417d63ac980fdf1d16f", "DinnerCode":"66bbea49e45d4307d4cde154"}
TheDen = {"LocationCode":"66bd0cf4e45d4307d4d6a533", "LunchCode":"66bd0cf4e45d4307d4d6a538"}
nutrientCodes = {'Calories':'682e0cba351d5305de8b5cc9', 'Protein' : '682e0cba351d5305de8b5cca'}

locationsMenuCodes.append(Commons)
locationsMenuCodes.append(Harris)
locationsMenuCodes.append(TheDen)

def getCommonsPeriodsUrl(date):
    ogurl = f"https://apiv4.dineoncampus.com/locations/5879069fee596f31b3dc146a/periods/?date={date}"
    return ogurl

def getHarrisPeriodsUrl(date):
    ogurl = f"https://apiv4.dineoncampus.com/locations/58790871ee596f31bcdc174d/periods/?date={date}"
    return ogurl

def getCommonsMenuUrl(perCode, date, locCode='5879069fee596f31b3dc146a'):
    url = f"https://apiv4.dineoncampus.com/locations/{locCode}/menu?date={date}&period={perCode}"
    return url

def getHarrisMenuUrl(perCode, date, locCode='58790871ee596f31bcdc174d'):
    url = f"https://apiv4.dineoncampus.com/locations/{locCode}/menu?date={date}&period={perCode}"
    return url

def getCommonsMenuFromPeriod(period, date):
    finalItems = []
    url = getCommonsMenuUrl(period, date)
    success, response = get_dining_api_response(url)
    periodName = response['period']['name']
    cats = response['period']['categories']
    for cat in cats:
        items = []
        for item in cat['items']:
            calories = next((nut for nut in item["nutrients"] if 'Calories' in nut['name']), None)
            protein = next((nut for nut in item["nutrients"] if 'Protein' in nut['name']), None)
            items.append(
                MenuItem(name=item['name'], calories=calories['value'], protein=protein['value'], today=False, tomorrow=True, harrisToday=False, harrisTomorrow=False, category=cat["name"], period=periodName)
            )
        finalItems.extend(items)
    return finalItems

def getHarrisMenuFromPeriod(period, date):
    finalItems = []
    url = getHarrisMenuUrl(period, date)
    success, response = get_dining_api_response(url)
    periodName = response['period']['name']
    cats = response['period']['categories']
    for cat in cats:
        items = []
        for item in cat['items']:
            calories = next((nut for nut in item["nutrients"] if 'Calories' in nut['name']), None)
            protein = next((nut for nut in item["nutrients"] if 'Protein' in nut['name']), None)
            items.append(
                MenuItem(name=item['name'], calories=calories['value'], protein=protein['value'], today=False, tomorrow=False, harrisToday=False, harrisTomorrow=True, category=cat["name"], period=periodName)
            )
        finalItems.extend(items)
    return finalItems

def getHarrisPeriods(date):
    periods = []
    success, response = get_dining_api_response(api_url=getHarrisPeriodsUrl(date))
    periodslist = response['periods']
    for per in periodslist:
        periods.append(per['id'])
    return periods


def getCommonsPeriods(date):
    periods = []
    success, response = get_dining_api_response(api_url=getCommonsPeriodsUrl(date))
    periodslist = response['periods']
    for per in periodslist:
        periods.append(per['id'])
    return periods

def getCommonsDailyMenu(date):
    final_items = []
    periods = getCommonsPeriods(date)
    # for per in periods:
    #     finalItems.extend(getCommonsMenuFromPeriod(per, date))
    final_items = getCommonsItemsUsingPeriodList(periods, date)
    return final_items

def getHarrisDailyMenu(date):
    final_items = []
    periods = getHarrisPeriods(date)
    # for per in periods:
    #     finalItems.extend(getHarrisMenuFromPeriod(per, date))
    final_items = getHarrisItemsUsingPeriodList(periods, date)
    return final_items

def getHarrisItemsUsingPeriodList(periods, date):
    final_items = []
    url_list = [getHarrisMenuUrl(per, date) for per in periods]
    success_overall, results = fetch_multiple_dining_json(url_list)

    if not success_overall:
        print("Failed to fetch menus")
        return []

    for url, (success, response) in results.items():
        if success:
            periodName = response['period']['name']
            for cat in response['period']['categories']:
                for item in cat['items']:
                    calories = next((nut for nut in item["nutrients"] if 'Calories' in nut['name']), None)
                    protein = next((nut for nut in item["nutrients"] if 'Protein' in nut['name']), None)
                    final_items.append(
                        MenuItem(
                            name=item['name'],
                            calories=calories['value'] if calories else None,
                            protein=protein['value'] if protein else None,
                            today=False,
                            tomorrow=False,
                            harrisToday=False,
                            harrisTomorrow=True,
                            category=cat["name"],
                            period=periodName
                        )
                    )
        else:
            print(f"Error fetching menu for {url}")

    return final_items

def getCommonsItemsUsingPeriodList(periods, date):
    final_items = []
    url_list = [getCommonsMenuUrl(per, date) for per in periods]
    success_overall, results = fetch_multiple_dining_json(url_list)

    if not success_overall:
        print("Failed to fetch menus")
        return []

    for url, (success, response) in results.items():
        if success:
            periodName = response['period']['name']
            for cat in response['period']['categories']:
                for item in cat['items']:
                    calories = next((nut for nut in item["nutrients"] if 'Calories' in nut['name']), None)
                    protein = next((nut for nut in item["nutrients"] if 'Protein' in nut['name']), None)
                    final_items.append(
                        MenuItem(
                            name=item['name'],
                            calories=calories['value'] if calories else None,
                            protein=protein['value'] if protein else None,
                            today=False,
                            tomorrow=True,
                            harrisToday=False,
                            harrisTomorrow=False,
                            category=cat["name"],
                            period=periodName
                        )
                    )
        else:
            print(f"Error fetching menu for {url}")

    return final_items