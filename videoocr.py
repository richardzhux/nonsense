import cv2
import pytesseract
import os
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from fuzzywuzzy import fuzz
import time
import numpy as np
from tqdm import tqdm

"""
video_path = ""
def extract_frames(video_path, output_folder, fps=10):
    os.makedirs(output_folder, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = frame_rate // fps
    
    count = 0
    success, image = cap.read()
    while success:
        if count % frame_interval == 0:
            frame_filename = f"{output_folder}/frame_{count:04d}.png"
            cv2.imwrite(frame_filename, image)
        count += 1
        success, image = cap.read()
    cap.release()
"""
import cv2
import pytesseract
import os
from tqdm import tqdm
import numpy as np
import psutil
import time
import threading

def monitor_resources(interval=1):
    """Monitor and print CPU and RAM usage at regular intervals."""
    while True:
        cpu_percent = psutil.cpu_percent(interval=interval)
        ram_percent = psutil.virtual_memory().percent
        print(f"CPU Usage: {cpu_percent}% | RAM Usage: {ram_percent}%")
        time.sleep(interval)  # Set the interval for checking resources




def perform_ocr(frame_folder):
    transcript = []
    frames = sorted([frame for frame in os.listdir(frame_folder) if frame.endswith('.png')])
    selected_frames = frames[::1]  # Process every nth frame

    # Start the resource monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor_resources, args=(1,), daemon=True)
    monitor_thread.start()

    for frame in tqdm(selected_frames, desc="Processing chat bubbles (every 1th frame)"):
    # Read each image frame
        img = cv2.imread(os.path.join(frame_folder, frame))
    
    # Use OCR to detect text in the image without filtering by color
        text = pytesseract.image_to_string(img, lang='chi_sim+eng').strip()
    
    # If any text is detected, append it to the transcript
        if text:
            transcript.append(f"Chat Message: {text}")

    return transcript



# Function to check similarity
def is_similar(a, b, threshold=0.9):
    return SequenceMatcher(None, a, b).ratio() > threshold

# Function to remove redundant lines
def remove_redundant_lines(transcript):
    filtered_transcript = []
    for line in transcript:
        if not filtered_transcript or not is_similar(line, filtered_transcript[-1]):
            filtered_transcript.append(line)
    return filtered_transcript

# Clustering function for near-duplicate lines
def cluster_and_filter(transcript):
    vectorizer = TfidfVectorizer().fit_transform(transcript)
    db = DBSCAN(eps=0.5, min_samples=1, metric="cosine").fit(vectorizer)
    
    clustered_transcript = []
    for cluster in set(db.labels_):
        clustered_lines = [transcript[i] for i, label in enumerate(db.labels_) if label == cluster]
        clustered_transcript.append(clustered_lines[0])  # Take the first line of each cluster as representative
    
    return clustered_transcript

# Main function to process frames and save transcript
def process_frames_to_text(frame_folder, output_text_path):
    # Perform OCR on each frame
    raw_transcript = perform_ocr(frame_folder)
    
    # Step 1: Remove exact or near-duplicate lines
    filtered_transcript = remove_redundant_lines(raw_transcript)
    
    # Step 2: Use clustering to remove any remaining near-duplicates
    final_transcript = cluster_and_filter(filtered_transcript)
    
    # Save the cleaned transcript to a text file
    with open(output_text_path, "w") as file:
        for line in final_transcript:
            file.write(line + "\n")

# Usage example
frame_folder = '/Users/rx/Desktop/Law 206/Quiz 5'  # Folder where your frames are located
output_text_path = '/Users/rx/Desktop/Quiz5'  # Output file path for the OCR transcript
process_frames_to_text(frame_folder, output_text_path)
