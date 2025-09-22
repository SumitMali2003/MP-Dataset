import os
import csv
import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS
from datetime import datetime

# Paths
dataset_folder = r"C:\Users\ACER\Desktop\dataset\audio"
output_csv = r"C:\Users\ACER\Desktop\dataset\output.csv"
hindi_csv = r"C:\Users\ACER\Desktop\dataset\hindi.csv"
marathi_csv = r"C:\Users\ACER\Desktop\dataset\marathi.csv"
output_audio_folder = r"C:\Users\ACER\Desktop\dataset\marathi_audio"
progress_log = r"C:\Users\ACER\Desktop\dataset\progress.log"
error_log = r"C:\Users\ACER\Desktop\dataset\error.log"

# Ensure output folders exist
os.makedirs(output_audio_folder, exist_ok=True)

# Load Whisper model
whisper_model = whisper.load_model("small")

# Logging functions
def log_progress(message):
    with open(progress_log, "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    print(message)

def log_error(file, error_message):
    with open(error_log, "a", encoding="utf-8") as elog:
        elog.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {file} -> {error_message}\n")
    log_progress(f"⚠️ Error logged for {file}")

log_progress("🚀 New run started.")

# Load existing CSV data
csv_data = {}
if os.path.exists(output_csv):
    with open(output_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_data[row["Filename"]] = row

# Collect existing audio
audio_data = {}
for audio_file in os.listdir(output_audio_folder):
    if audio_file.endswith("_mr.mp3"):
        original_name = audio_file.replace("_mr.mp3", ".mp3")
        audio_data[original_name] = os.path.join(output_audio_folder, audio_file)

# Open all CSVs
with open(output_csv, mode="w", encoding="utf-8", newline="") as fout, \
     open(hindi_csv, mode="w", encoding="utf-8", newline="") as fhindi, \
     open(marathi_csv, mode="w", encoding="utf-8", newline="") as fmarathi:

    writer_all = csv.writer(fout)
    writer_hindi = csv.writer(fhindi)
    writer_marathi = csv.writer(fmarathi)

    # Write headers
    writer_all.writerow(["Filename", "Hindi Text", "Marathi Translation", "Marathi Audio File"])
    writer_hindi.writerow(["Filename", "Hindi Text"])
    writer_marathi.writerow(["Filename", "Marathi Translation"])

    # Process all mp3 files
    for file in os.listdir(dataset_folder):
        if not file.endswith(".mp3"):
            continue

        file_path = os.path.join(dataset_folder, file)
        marathi_audio_file = os.path.join(output_audio_folder, file.replace(".mp3", "_mr.mp3"))

        hindi_text, marathi_text = None, None

        try:
            # Case A: Already processed → reuse
            if file in csv_data and os.path.exists(marathi_audio_file):
                hindi_text = csv_data[file]["Hindi Text"]
                marathi_text = csv_data[file]["Marathi Translation"]
                log_progress(f"✅ Skipping (already processed): {file}")

            # Case B: Audio exists but CSV missing → rebuild CSV row
            elif file in audio_data and file not in csv_data:
                log_progress(f"♻️ Rebuilding CSV entry for: {file}")
                result = whisper_model.transcribe(file_path, language="hi")
                hindi_text = result["text"].strip()
                marathi_text = GoogleTranslator(source="hi", target="mr").translate(hindi_text)

            # Case C: CSV exists but audio missing → rebuild audio
            elif file in csv_data and not os.path.exists(marathi_audio_file):
                log_progress(f"🔊 Rebuilding audio for: {file}")
                hindi_text = csv_data[file]["Hindi Text"]
                marathi_text = csv_data[file]["Marathi Translation"]
                marathi_tts = gTTS(text=marathi_text, lang="mr")
                marathi_tts.save(marathi_audio_file)

            # Case D: Completely new file
            else:
                log_progress(f"🎵 Processing new file: {file}")
                result = whisper_model.transcribe(file_path, language="hi")
                hindi_text = result["text"].strip()
                marathi_text = GoogleTranslator(source="hi", target="mr").translate(hindi_text)

                marathi_tts = gTTS(text=marathi_text, lang="mr")
                marathi_tts.save(marathi_audio_file)

            # Write rows into all CSVs
            if hindi_text and marathi_text:
                writer_all.writerow([file, hindi_text, marathi_text, marathi_audio_file])
                writer_hindi.writerow([file, hindi_text])
                writer_marathi.writerow([file, marathi_text])

        except Exception as e:
            log_error(file, str(e))
            continue

log_progress("✅ All CSVs and Marathi audio synced successfully.")
