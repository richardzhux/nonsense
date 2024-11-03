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

def is_chat_bubble(img, bubble_color):
    """Detects and extracts only blue or white chat bubbles based on color."""
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    if bubble_color == 'blue':
        lower_blue = np.array([105, 160, 180])
        upper_blue = np.array([115, 255, 255])
        mask = cv2.inRange(hsv_img, lower_blue, upper_blue)
    elif bubble_color == 'white':
        lower_white = np.array([0, 0, 240])
        upper_white = np.array([180, 10, 255])
        mask = cv2.inRange(hsv_img, lower_white, upper_white)
    else:
        return None

    result = cv2.bitwise_and(img, img, mask=mask)
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    processed_bubble = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    return processed_bubble

def perform_ocr(frame_folder):
    transcript = []
    frames = sorted([frame for frame in os.listdir(frame_folder) if frame.endswith('.png')])
    selected_frames = frames[::5]  # Process every 5th frame

    # Start the resource monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor_resources, args=(1,), daemon=True)
    monitor_thread.start()

    # Using tqdm to add a progress bar to the loop
    for frame in tqdm(selected_frames, desc="Processing chat bubbles (every 5th frame)"):
        img = cv2.imread(os.path.join(frame_folder, frame))

        blue_bubble = is_chat_bubble(img, 'blue')
        white_bubble = is_chat_bubble(img, 'white')

        text_blue = pytesseract.image_to_string(blue_bubble, lang='chi_sim+eng').strip()
        if text_blue:
            transcript.append(f"Blue Bubble (Your Message): {text_blue}")

        text_white = pytesseract.image_to_string(white_bubble, lang='chi_sim+eng').strip()
        if text_white:
            transcript.append(f"White Bubble (Other’s Message): {text_white}")
    
    print("OCR processing complete.")
    return transcript



""" Old ETA counter
def perform_ocr(frame_folder):
    transcript = []
    frames = sorted([frame for frame in os.listdir(frame_folder) if frame.endswith('.png')])
    total_frames = len(frames)
    
    start_time = time.time()  # Start the timer
    
    for idx, frame in enumerate(frames):
        img = cv2.imread(os.path.join(frame_folder, frame))
        # Specify both Simplified Chinese and English
        text = pytesseract.image_to_string(img, lang='chi_sim+eng').strip()
        
        if text:
            transcript.append(text)
        
        # Estimate time remaining every 50 frames
        if (idx + 1) % 50 == 0:
            elapsed_time = time.time() - start_time
            avg_time_per_frame = elapsed_time / (idx + 1)
            remaining_time = avg_time_per_frame * (total_frames - (idx + 1))
            print(f"Processed {idx + 1}/{total_frames} frames... Estimated time remaining: {remaining_time:.2f} seconds")
    
    print("OCR processing complete.")
    return transcript
"""

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
frame_folder = ""  # Folder where your frames are located
output_text_path = ""  # Output file path for the OCR transcript
process_frames_to_text(frame_folder, output_text_path)
