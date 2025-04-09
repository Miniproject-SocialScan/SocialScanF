import os
import pandas as pd
import numpy as np
from google.generativeai import configure, GenerativeModel
import streamlit as st

# ✅ Load and preprocess data
DATA_PATH = 'dataset1_train.csv'
data = pd.read_csv(DATA_PATH)

# ✅ Select relevant columns
columns_to_keep = ['user_info.Username', 'user_info.Category', 'user_info.Related Profiles'] + \
                  [f'images[{i}].Likes' for i in range(12)] + [f'images[{i}].Caption' for i in range(12)]
data = data[columns_to_keep]

# ✅ Handle missing values and convert data types
for i in range(12):
    data[f'images[{i}].Likes'] = pd.to_numeric(data[f'images[{i}].Likes'], errors='coerce').fillna(0)
    data[f'images[{i}].Caption'] = data[f'images[{i}].Caption'].fillna("")

# ✅ Analyze behavior function
def analyze_behavior(user):
    # Filter data for the selected user
    user_data = data[data['user_info.Username'] == user]
    if user_data.empty:
        return None
    
    # Fetch user category and related profiles
    category = user_data['user_info.Category'].iloc[0] if 'user_info.Category' in user_data.columns else "Unknown"
    related_profiles = user_data['user_info.Related Profiles'].iloc[0] if 'user_info.Related Profiles' in user_data.columns else "None"
    
    # Extract likes and captions
    likes_and_captions = []
    for i in range(12):
        likes_column = f'images[{i}].Likes'
        caption_column = f'images[{i}].Caption'
        
        # Check if the columns exist in the dataset
        if likes_column in user_data.columns and caption_column in user_data.columns:
            likes = user_data[likes_column].iloc[0]
            caption = user_data[caption_column].iloc[0]
            
            # Ensure likes are numeric and captions are strings
            if pd.notna(likes) and pd.notna(caption):
                likes_and_captions.append((int(likes), str(caption)))
    
    if not likes_and_captions:
        return None
    
    # Calculate average likes
    avg_likes = sum(like for like, _ in likes_and_captions) / len(likes_and_captions)
    
    # Sort likes and captions in descending order of likes
    sorted_likes_captions = sorted(likes_and_captions, key=lambda x: x[0], reverse=True)

    return {
        'category': category,
        'related_profiles': related_profiles,
        'avg_likes': avg_likes,
        'sorted_likes_captions': sorted_likes_captions
    }

# ✅ Generate prompt using LLM
def generate_prompt(username, query):
    behavior = analyze_behavior(username)
    if not behavior:
        return "No data available for the selected user."
    
    prompt = f"Generate a response for {username}, a {behavior['category']} influencer. "
    prompt += f"Related profiles: {behavior['related_profiles']}. "
    prompt += f"Top performing captions include: {', '.join([caption for _, caption in behavior['sorted_likes_captions'][:5]])}. "
    prompt += f"Average engagement score: {behavior['avg_likes']:.2f}. Query: {query}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error generating content: {e}"

# ✅ Streamlit UI
st.title("📲 LLM Fine-Tuning for Social Media Analysis")

# Select username
usernames = data['user_info.Username'].unique()
selected_user = st.selectbox("👤 Select a username", usernames)

# Input for user query
query = st.text_input("💬 Ask about the user behavior:")

if st.button("🚀 Analyze"):
    behavior = analyze_behavior(selected_user)
    if behavior:
        # Display user behavior analysis
        st.write("### 🔎 User Behavior Analysis:")
        st.write(f"**Category:** {behavior['category']}")
        st.write(f"**Related Profiles:** {behavior['related_profiles']}")
        st.write(f"**Average Engagement Score:** {behavior['avg_likes']:.2f}")

        # Display likes and captions in a table format
        st.write("❤️ **Likes and Captions (Sorted by Likes):**")
        likes_captions_df = pd.DataFrame(behavior['sorted_likes_captions'], columns=["Likes", "Caption"])
        st.table(likes_captions_df)

        # Generate LLM response if query is provided
        if query:
            st.write("### 🤖 LLM Response:")
            result = generate_prompt(selected_user, query)
            st.write(result)
    else:
        st.write("⚠️ No data available for the selected user.")
