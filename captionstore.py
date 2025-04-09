import json
import httpx
import time
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://agrawa271:Arpit123@cluster0.oxpf0kb.mongodb.net/"  # Ensure MongoDB is running locally
client_mongo = MongoClient(MONGO_URI)
db = client_mongo["instagram_user"]  # Database name
collection = db["users"]  # Collection name

# Define the HTTP client with updated headers
headers = {
    "x-ig-app-id": "936619743392459",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "*/*",
    "Referer": "https://www.instagram.com/",
    "Origin": "https://www.instagram.com",
    "Cookie": "sessionid=YOUR_SESSION_ID_HERE"  # Replace with your actual session ID
}
client = httpx.Client(headers=headers)

def scrape_user(username: str):
    """Scrape Instagram user's data."""
    try:
        result = client.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}")

        if result.status_code != 200:
            print(f"Failed to retrieve data for {username}. Status code: {result.status_code}")
            return None

        data = json.loads(result.content)
        user_info = data.get("data", {}).get("user", {})
        if not user_info:
            print(f"User {username} not found.")
            return None

        # Extract User Details
        user = {
            "Username": user_info.get("username", "N/A"),
            "Full Name": user_info.get("full_name", "N/A"),
            "ID": user_info.get("id", "N/A"),
            "Followers": user_info.get("edge_followed_by", {}).get("count", 0),
            "Following": user_info.get("edge_follow", {}).get("count", 0),
            "Biography": user_info.get("biography", "N/A"),
            "Category": user_info.get("category_name", "N/A"),
            "Is Private": user_info.get("is_private", False),
            "Is Verified": user_info.get("is_verified", False),
            "Related Profiles": ", ".join(profile.get("node", {}).get("username", "N/A").replace("\u00A0", " ") 
                                           for profile in user_info.get("edge_related_profiles", {}).get("edges", []))
        }

        # Extract Images and Captions into One Column
        images = user_info.get("edge_owner_to_timeline_media", {}).get("edges", [])
        image_info = {
            "Images": [{
                "ID": image.get("node", {}).get("id", "N/A"),
                "Likes": image.get("node", {}).get("edge_liked_by", {}).get("count", 0),
                "Caption": image.get("node", {}).get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "N/A")
            } for image in images]
        }
        
        user["Images"] = image_info["Images"]
        return user
    except Exception as e:
        print(f"Error scraping {username}: {e}")
        return None

def save_to_mongo(user_info):
    """Save data to MongoDB."""
    if not user_info:
        return

    user_data = {
        "user_info": user_info,
        "timestamp": time.time(),
    }

    # Check if user exists
    existing_user = collection.find_one({"user_info.Username": user_info.get("Username")})
    if existing_user:
        collection.update_one(
            {"user_info.Username": user_info.get("Username")},
            {"$set": user_data}
        )
        print(f"Updated data for {user_info['Username']} in MongoDB.")
    else:
        collection.insert_one(user_data)
        print(f"Inserted new data for {user_info['Username']} into MongoDB.")

def main():
    usernames = ["johndelony",
"joejonas",
"emwallbank",
"kellyclarksonshow",
"primevideo",
"jayshetty",
"thespacega",
"thefastsaga",
"jimmykimmel",
"cnn",
"itsjvke",
"danawhite",
"bbnomula",
"natebargatze",
"fallontonight",
"askvinh",
"simonsinek",
"calebrownnnnn",
"doc_amen",
"shredhappens",
"shredhappens",
"nicolescherzinger",
"anthonygargiula",
"rebelwilson",
"brody_wellmaker",
"ciara",
"derekhough",
"therock",
"kevinhart4real",
"jasonbankscomedy",
"marlonwayans",
"dcofficial",
"parishilton",
"jamesarthur23",
"crystalritchsonphoto",
"naturbaker",
"rea_nolan",
"pastordrewsams",
"sabrainslicht",
"roksanarazavifilm",
"youngblood38_",
"gavinwhite___",
"jo_pat_01",
"alex_chiz1",
"allisonmsilk",
"chrisreed619",
"wardencinematics",
"curriegraham",
"dritchson_",
"stankirschstudios",
"annaliese_levy",
"sunilperkash",
"bianca.francesca",
"toddrice",
"realrobramsay",
"jenny.stead",
"kimberlytarnold",
"christophergardner",
"jonathankoensgen",
"squashy_nice",
"noahwilsonlive",
"nicholastheward",
"mspike",
"theestatedirector",
"navi_the_north",
"jamesward_79",
"mr.lukeg",
"brandonbehappy",
"andreapezzillo",
"jjjonathankim",
"katvonpire",
"tomasosanelli",
"alices_tattoo",
"bjmcelhaney",
"ninazivkovic11",
"3star_productions",
"drewmylrea",
"mrgarelick",
"natwaart",
"tatianacinquino",
"p6yton",
"seeuatnoon",
"jackreacherbooks",
"reacherprimevideo",
] 
 # Add usernames
    for username in usernames:
        print(f"Scraping data for {username}...")
        user_info = scrape_user(username)
        if user_info:
            save_to_mongo(user_info)
        time.sleep(2)  # Avoid rate limits
    print("Data storage complete.")

if __name__ == "__main__":
    main()
