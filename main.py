import firebase_admin
import time
import json
import re
import os
import concurrent.futures
from datetime import datetime, timedelta
from collections import defaultdict
from openStatusScrape import *
from menuScrape import getDailyMenu
from MenuItem import MenuItem
from firebase_admin import credentials, messaging, firestore
from firebase_admin.exceptions import FirebaseError

# Get the credentials JSON string from the environment variable
firebase_creds_json = os.getenv("FIREBASE_SECRET_KEY")

# Convert the JSON string to a dict
creds_dict = json.loads(firebase_creds_json)

# Create a credentials.Certificate object from the dict
cred = credentials.Certificate(creds_dict)

# Initialize Firebase app only if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

open_ref = db.collection("OpenStatus").document("Commons")
items_menu_ref = db.collection("Items")

def send_notification_batch(notifications):
    """Send multiple notifications in parallel using ThreadPoolExecutor"""
    success_count = 0
    failure_count = 0
    results = []
    
    # Use ThreadPoolExecutor for parallel processing
    # Limiting to 10 concurrent sends to avoid overwhelming the API
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_msg = {
            executor.submit(messaging.send, message): i 
            for i, message in enumerate(notifications)
        }
        
        for future in concurrent.futures.as_completed(future_to_msg):
            msg_index = future_to_msg[future]
            try:
                result = future.result()
                results.append(result)
                success_count += 1
                if success_count % 10 == 0:  # Log progress every 10 successful sends
                    print(f"Progress: {success_count}/{len(notifications)} notifications sent successfully")
            except Exception as e:
                failure_count += 1
                print(f"Error sending notification {msg_index}: {e}")
    
    print(f"Completed: {success_count} successful, {failure_count} failed")
    return results

def send_notifications():
    start_time = time.time()
    
    # 1. Get all items available today in one query
    today_items_ref = db.collection('Items').where('today', '==', 'True')
    today_items_snapshot = today_items_ref.get()
    today_item_ids = {doc.id: doc.to_dict() for doc in today_items_snapshot}
    
    print(f"Items available today: {len(today_item_ids)}")
    
    if not today_item_ids:
        print("No items available today, skipping notifications")
        return
    
    # 2. Get all users in one query
    users_ref = db.collection('Users')
    users_snapshot = users_ref.get()
    
    # 3. Prepare notifications for all eligible users
    notifications = []
    user_count = 0

    for user_doc in users_snapshot:
        user_data = user_doc.to_dict()
        user_id = user_doc.id

        if 'fcmToken' not in user_data or 'favorites' not in user_data or user_data.get('dailyFavsNotificationsEnabled') is not True:
            continue
        
        user_token = user_data['fcmToken']
        favorite_items = user_data.get('favorites', [])
        
        available_favorites = [item_id for item_id in favorite_items if item_id in today_item_ids]

        if not available_favorites:
            continue
            
        user_count += 1
        
        # Construct notification message
        if len(available_favorites) == 1:
            item_name = today_item_ids[available_favorites[0]].get('name', 'Unknown Item')
            title = f"Item: {item_name} is available today!"
            body = "Come check it out!"
        else:
            title = f"{len(available_favorites)} of your favorites are available today!"
            item_names = [today_item_ids[item_id].get('name', 'Unknown Item') for item_id in available_favorites[:3]]
            body = f"{', '.join(item_names[:2])}"
            if len(item_names) > 2:
                body += f" and {len(available_favorites) - 2} more!"
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data={
                'type': 'favorite_items_available',
                'available_favorites': ','.join(available_favorites),
                'count': str(len(available_favorites))
            },
            token=user_token
        )
        
        notifications.append(message)
    
    print(f"Found {user_count} users with favorites available today")
    
    # 4. Send all notifications in parallel
    if notifications:
        print(f"Sending {len(notifications)} notifications...")
        send_notification_batch(notifications)
    
    end_time = time.time()
    print(f"Execution completed in {end_time - start_time:.2f} seconds")

def getKeywords(str1, str2, str3):
    def generate_prefixes(text):
        text = re.sub(r'[^\w\s]', '', text.lower())  # clean text
        prefixes = set()
        for i in range(1, len(text) + 1):
            prefixes.add(text[:i])
        return prefixes

    keywords = set()
    for s in [str1, str2, str3]:
        keywords.update(generate_prefixes(s))

    return sorted(list(keywords))

def getPastRatings():
    doc_ref = db.collection("Ratings").document("WeeklyAvgScores")

    doc = doc_ref.get()
    if doc.exists:
        print(f"Document data: {doc.to_dict()}")
    else:
        print("No such document!")
    
    return doc.to_dict()

def getCurrentRating():
    doc_ref = db.collection("Ratings").document("CurrentRatings")

    doc = doc_ref.get()
    if doc.exists:
        print(f"Document data: {doc.to_dict()}")
    else:
        print("No such document!")

    return doc.to_dict()

def setWeeklyHours(location, date):
    weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    hours = getWeeklyHours(location, date)
    finalDict = {}
    for i in hours:
        finalDict[f"{weekdays[i["day"]]}"] = i['hours']
    try:
        db.collection("OpenStatus").document(location).set(finalDict)
    except:
        print("Error with hours")

def commit_in_batches(docs, update_fn):
    batch = db.batch()
    count = 0
    for doc in docs:
        update_fn(batch, doc)
        count += 1
        if count == 500:
            batch.commit()
            batch = db.batch()
            count = 0
    if count > 0:
        batch.commit()

def todayTomorrowUpdate():
    # Step 1: today=True & tomorrow=False -> today=False
    docs = db.collection('Items').where('today', '==', True).where('tomorrow', '==', False).stream()
    commit_in_batches(docs, lambda batch, doc: batch.update(doc.reference, {'today': False}))

    # Step 2: tomorrow=True -> today=True, tomorrow=False
    docs = db.collection('Items').where('tomorrow', '==', True).stream()
    commit_in_batches(docs, lambda batch, doc: batch.update(doc.reference, {
        'today': True,
        'tomorrow': False
    }))

    # # Step 3: harrisToday=True & harrisTomorrow=False -> harrisToday=False
    # docs = db.collection('Items').where('harrisToday', '==', True).where('harrisTomorrow', '==', False).stream()
    # commit_in_batches(docs, lambda batch, doc: batch.update(doc.reference, {'harrisToday': False}))

    # # Step 4: harrisTomorrow=True -> harrisToday=True, harrisTomorrow=False
    # docs = db.collection('Items').where('harrisTomorrow', '==', True).stream()
    # commit_in_batches(docs, lambda batch, doc: batch.update(doc.reference, {
    #     'harrisToday': True,
    #     'harrisTomorrow': False
    # }))

def mergeItems(list1, list2):
    merged = {}
    
    for item in list1 + list2:
        if item.id not in merged:
            # First time seeing this ID, store it
            merged[item.id] = item
        else:
            # Merge logic
            existing = merged[item.id]
            existing.tomorrow = existing.tomorrow or item.tomorrow
            existing.harrisTomorrow = existing.harrisTomorrow or item.harrisTomorrow
            # Optional: If you'd like to combine other fields or prefer one version, handle that here

    return list(merged.values())

def updateFirebase(date):
    items = getDailyMenu(date)
    print(items)
    harrisItems = getDailyHarrisMenu(date)
    print("Harris Items")
    allItems = mergeItems(items1=items, items2=harrisItems)
    # items = [MenuItem(name="Test", calories=34, period="Breakfast", protein=90, category="MainLine", today='False', tomorrow="True")]
    batch = db.batch()
    collection_ref = db.collection('Items')

    for index, item in enumerate(items):
        doc_ref = collection_ref.document(item.id)

        data = item.toJson()
        del data['today']
        del data['harrisToday']
        data['lastSeen'] = '2025-05-20T20:01:32Z'
        data['keywords'] = getKeywords(item.name, item.category, item.period)
        batch.set(doc_ref, data, merge=True)

        if (index + 1) % 500 == 0:
            batch.commit()
            batch = db.batch()

    if (index + 1) % 500 != 0:
        batch.commit()

def dailyMenuOperation(date):
    todayTomorrowUpdate()
    updateFirebase(date)

def dailyNotificationOperation():
    send_notifications()

def dailyHoursOperation(date):
    # Change for
    setWeeklyHours(location="Commons", date=f"{date}")
    setWeeklyHours(location="Harris", date=f"{date}")

def dailyRatingOperation(date):
    pastRatings = getPastRatings()
    currentRatings = getCurrentRating()
    newPastRatings = {'3dayPast': pastRatings["2dayPast"], '2dayPast': pastRatings["1dayPast"], '4dayPast': pastRatings["3dayPast"], '5dayPast': pastRatings["4dayPast"], '1dayPast': currentRatings["dailyAvg"], '6dayPast': pastRatings["5dayPast"]}
    newCurrentRatings = {'numDailyRatings': 0, 'lastRating': '2025-04-19T11:57:52-05:00', 'crowdScore': 0.5, 'tasteScore': 0.5, 'numRatings': 0, 'diningScore': 0.5, 'abundanceScore': 0.5, 'dailyAvg': 0.5}
    try: 
        db.collection("Ratings").document("CurrentDay").set({"date" : convert_to_firestore_timestamp(date)})
        db.collection("Ratings").document("CurrentRatings").set(newCurrentRatings)
        db.collection("Ratings").document("WeeklyAvgScores").set(newPastRatings)
    except:
        print("Error with Ratings")

def dailyOperation():
    date = dateIterator()
    try:
        dailyMenuOperation(date)
    except:
        print('Error getting menus')
    try:
        dailyRatingOperation(date)
    except:
        print('Error with ratings')
    try:
        dailyNotificationOperation()
    except:
        print('Error with notifications')
    try:
        dailyHoursOperation(date)
    except:
        print('Error with hours')

def dateIterator():
    today = datetime.now()
    timewewant = today
    formatted_date = timewewant.strftime("%Y-%m-%d")
    return formatted_date

def convert_to_firestore_timestamp(date_str):
    # Parse the string to a datetime object
    dt = datetime.strptime(date_str, "%Y-%m-%d")

    # Firestore can accept Python datetime objects directly
    return dt


dailyOperation()