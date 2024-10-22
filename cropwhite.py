import os
from PIL import Image

# Define the folder where your images are stored
input_folder = '/Users/rx/Desktop/Law 206 Quiz'
output_folder = '/Users/rx/Desktop/Law 206 Quiz Crop'

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Set the crop coordinates (left, top, right, bottom)
# You need to manually identify these based on the area you want to crop in the first image
crop_box = (1120, 626, 3024-760, 1900)  # Replace with actual values, e.g., (50, 100, 300, 400)

# Loop through all files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".jpg") or filename.endswith(".png"):  # add any other file types you need
        # Open an image file
        img_path = os.path.join(input_folder, filename)
        with Image.open(img_path) as img:
            # Crop the image to the desired area
            cropped_img = img.crop(crop_box)

            # Save the cropped image to the output folder
            output_path = os.path.join(output_folder, filename)
            cropped_img.save(output_path)

        print(f"Cropped and saved: {filename}")
