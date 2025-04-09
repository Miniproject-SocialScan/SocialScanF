import streamlit as st
import json
import httpx
from PIL import Image
from io import BytesIO
import time
from pymongo import MongoClient

# MongoDB Connection (Local or Atlas)
MONGO_URI = "mongodb+srv://agrawa271:Arpit123@cluster0.oxpf0kb.mongodb.net/"  # Replace with your MongoDB credentials
client_mongo = MongoClient(MONGO_URI)
db = client_mongo["instagram_user"]  # Database name
collection = db["users"]  # Collection name

# Define the HTTP client
client = httpx.Client(
    headers={
        "x-ig-app-id": "936619743392459",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "/",
    }
)

def scrape_user(username: str):
    """Scrape Instagram user's data and extract relevant info, including all available images, captions, and comments."""
    try:
        result = client.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}")

        if result.status_code != 200:
            return f"Failed to retrieve data. Status code: {result.status_code}", [], []

        try:
            data = json.loads(result.content)
        except json.JSONDecodeError:
            return "Error decoding JSON response from the server.", [], []

        user_info = data.get("data", {}).get("user", {})
        if not user_info:
            return "User not found or unable to retrieve data.", [], []

        # Extract User Details
        user = {
            "Username": user_info.get("username", "N/A"),
            "Full Name": user_info.get("full_name", "N/A"),
            "ID": user_info.get("id", "N/A"),
            "Category": user_info.get("category_name", "N/A"),
            "Business Category": user_info.get("business_category_name", "N/A"),
            "Phone": user_info.get("business_phone_number", "N/A"),
            "Email": user_info.get("business_email", "N/A"),
            "Biography": user_info.get("biography", "N/A"),
            "Bio Links": [link.get("url") for link in user_info.get("bio_links", []) if link.get("url")],
            "Homepage": user_info.get("external_url", "N/A"),
            "Followers": f"{user_info.get('edge_followed_by', {}).get('count', 0):,}",
            "Following": f"{user_info.get('edge_follow', {}).get('count', 0):,}",
            "Facebook ID": user_info.get("fbid", "N/A"),
            "Is Private": user_info.get("is_private", "N/A"),
            "Is Verified": user_info.get("is_verified", "N/A"),
            "Profile Image": user_info.get("profile_pic_url_hd", "N/A"),
            "Video Count": user_info.get("edge_felix_video_timeline", {}).get("count", 0),
            "Image Count": user_info.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "Saved Count": user_info.get("edge_saved_media", {}).get("count", 0),
            "Collections Count": user_info.get("edge_saved_media", {}).get("count", 0),
            "Related Profiles": [profile.get("node", {}).get("username", "N/A") for profile in user_info.get("edge_related_profiles", {}).get("edges", [])],
        }

        # Extract Images, Captions, and Comments
        images = user_info.get("edge_owner_to_timeline_media", {}).get("edges", [])
        image_info = []

        for image in images:
            image_node = image.get("node", {})
            comments = []
            if image_node.get("edge_media_to_comment", {}).get("count", 0) > 0:
                comments_query = client.get(f"https://i.instagram.com/api/v1/media/{image_node.get('id')}/comments/")
                if comments_query.status_code == 200:
                    comments_data = comments_query.json()
                    comments = [comment.get("text", "") for comment in comments_data.get("comments", [])]

            image_info.append({
                "ID": image_node.get("id", "N/A"),
                "Source": image_node.get("display_url", "N/A"),
                "Likes": image_node.get("edge_liked_by", {}).get("count", 0),
                "Caption": image_node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "N/A"),
                "Comments": comments,
            })

        return user, image_info
    except Exception as e:
        return f"An error occurred: {e}", [], []
    

def fetch_image(url):
    """Fetch image from URL and return PIL Image object, or a placeholder if failed."""
    try:
        response = client.get(url, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception:
        pass  # Handle errors silently

    # Return a placeholder image if loading fails
    return Image.open("placeholder.png")  # Ensure placeholder.png exists


def save_to_mongo(user_info, images):
    """Save scraped data to MongoDB."""
    if isinstance(user_info, str):  # If there's an error message, don't save
        st.error(user_info)
        return

    user_data = {
        "user_info": user_info,
        "images": images,
        "timestamp": time.time(),
    }

    # Check if user already exists in the database
    existing_user = collection.find_one({"user_info.Username": user_info["Username"]})
    if existing_user:
        st.warning("User data already exists in MongoDB. Updating record.")
        collection.update_one(
            {"user_info.Username": user_info["Username"]},
            {"$set": user_data}
        )
    else:
        collection.insert_one(user_data)
        st.success("Data successfully saved to MongoDB")

def display_user_info(user_info):
    """Display the user's information"""
    st.subheader("User Information")
    if isinstance(user_info, str):
        st.error(user_info)
    else:
        for key, value in user_info.items():
            st.write(f"{key}:** {value}")
        
        if user_info.get("Profile Image"):
            try:
                response = client.get(user_info.get("Profile Image"))
                img = Image.open(BytesIO(response.content))
                st.image(img, caption="Profile Picture", use_container_width=True)
            except Exception as e:
                st.error(f"Error loading profile image: {e}")


def display_media_grid(media_list, columns=3):
    """Display images in a responsive Instagram-style grid with Post ID, Likes, Captions, and Comments."""
    st.subheader("User's Latest Posts")

    if not media_list:
        st.warning("No images found.")
        return

    rows = [media_list[i:i+columns] for i in range(0, len(media_list), columns)]  # Split into rows
    
    for row in rows:
        cols = st.columns(columns)  # Create columns dynamically

        for idx, media in enumerate(row):
            with cols[idx]:  # Place each image in its respective column
                img = fetch_image(media["Source"])  # Fetch the image
                st.image(img, use_container_width=True)  # Ensure it fits the column width
                st.write(f"❤ {media['Likes']} Likes**")
                st.caption(f"📌 Post ID: {media['ID']}")
                
                # Display caption in an expander
                with st.expander("View Caption"):
                    st.write(f"{media['Caption']}")

                # Display comments in an expander
                if media["Comments"]:
                    with st.expander(f"View Comments ({len(media['Comments'])})"):
                        for comment in media["Comments"]:
                            st.write(f"- {comment}")

def main():
    st.title("SocialScan")
    username = st.text_input("Enter the Instagram username", placeholder="Username")
    
    if st.button("Scrape Data"):
        if username:
            with st.spinner("Scraping data..."):
                user_info, images = scrape_user(username)

            # Save to MongoDB
            save_to_mongo(user_info, images)

            # Display user info and images
            display_user_info(user_info)
            # display_media(images)  # ✅ Ensures all images are shown

            display_media_grid(images)  # ✅ Ensures images are displayed in a grid

        else:
            st.error("Please enter a valid username")
# def scrape_user(username: str):
#     """Scrape Instagram user's data and extract relevant info, including all available images, captions, and comments."""
#     try:
#         result = client.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}")
#         if result.status_code != 200:
#             return f"Failed to retrieve data. Status code: {result.status_code}", [], []
#         try:
#             data = json.loads(result.content)
#         except json.JSONDecodeError:
#             return "Error decoding JSON response from the server.", [], []
#         user_info = data.get("data", {}).get("user", {})
#         if not user_info:
#             return "User not found or unable to retrieve data.", [], []
#         # Extract User Details
#         user = {
#             "Username": user_info.get("username", "N/A"),
#             "Full Name": user_info.get("full_name", "N/A"),
#             "ID": user_info.get("id", "N/A"),
#             "Category": user_info.get("category_name", "N/A"),
#             "Business Category": user_info.get("business_category_name", "N/A"),
#             "Phone": user_info.get("business_phone_number", "N/A"),
#             "Email": user_info.get("business_email", "N/A"),
#             "Biography": user_info.get("biography", "N/A"),
#             "Bio Links": [link.get("url") for link in user_info.get("bio_links", []) if link.get("url")],
#             "Homepage": user_info.get("external_url", "N/A"),
#             "Followers": f"{user_info.get('edge_followed_by', {}).get('count', 0):,}",
#             "Following": f"{user_info.get('edge_follow', {}).get('count', 0):,}",
#             "Facebook ID": user_info.get("fbid", "N/A"),
#             "Is Private": user_info.get("is_private", "N/A"),
#             "Is Verified": user_info.get("is_verified", "N/A"),
#             "Profile Image": user_info.get("profile_pic_url_hd", "N/A"),
#             "Video Count": user_info.get("edge_felix_video_timeline", {}).get("count", 0),
#             "Image Count": user_info.get("edge_owner_to_timeline_media", {}).get("count", 0),
#             "Saved Count": user_info.get("edge_saved_media", {}).get("count", 0),
#             "Collections Count": user_info.get("edge_saved_media", {}).get("count", 0),
#             "Related Profiles": [profile.get("node", {}).get("username", "N/A") for profile in user_info.get("edge_related_profiles", {}).get("edges", [])],
#         }
#         # Extract Images, Captions, and Comments
#         images = user_info.get("edge_owner_to_timeline_media", {}).get("edges", [])
#         image_info = []

#         for image in images:
#             image_node = image.get("node", {})
#             comments = []
#             if image_node.get("edge_media_to_comment", {}).get("count", 0) > 0:
#                 comments_query = client.get(f"https://i.instagram.com/api/v1/media/{image_node.get('id')}/comments/")
#                 if comments_query.status_code == 200:
#                     comments_data = comments_query.json()
#                     comments = [comment.get("text", "") for comment in comments_data.get("comments", [])]

#             image_info.append({
#                 "ID": image_node.get("id", "N/A"),
#                 "Source": image_node.get("display_url", "N/A"),
#                 "Likes": image_node.get("edge_liked_by", {}).get("count", 0),
#                 "Caption": image_node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "N/A"),
#                 "Comments": comments,
#             })

#         return user, image_info
#     except Exception as e:
#         return f"An error occurred: {e}", [], []

if __name__ == "__main__":
    main()