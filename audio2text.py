import whisper
import torch

# Force Whisper to run on CPU to avoid MPS indexing issues
device = "cpu"
print(f"Using device: {device}")

# Load Whisper Model
model = whisper.load_model("medium").to(device)

# Transcribe the Audio File (Pass file path, NOT tensor)
result = model.transcribe("/Users/rx/Downloads/bart.m4a", word_timestamps=False)

# Parse Transcription Segments
transcript_data = result["segments"]  # List of timestamped segments

# Initialize List for Formatted Transcript
formatted_transcript = []

# Generate Conversation Format with Timestamps
for segment in transcript_data:
    start_time = segment["start"]
    text = segment["text"]
    formatted_transcript.append(f"[{start_time:.2f}s] {text}")

# Convert List to String
final_transcript = "\n".join(formatted_transcript)

# Save as **Text File**
output_file = "/Users/rx/Downloads/transcript.txt"  # Change this to your desired path
with open(output_file, "w", encoding="utf-8") as txt_file:
    txt_file.write(final_transcript)

# Print Completion Message
print(f"Transcription saved as {output_file}")
