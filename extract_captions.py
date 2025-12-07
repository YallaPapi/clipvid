import anthropic
import base64
import csv
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env file from same directory as script
load_dotenv(Path(__file__).parent / ".env")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MODEL = "claude-sonnet-4-5-20250929"

REWRITE_PROMPT = """Rewrite this caption. Rules:
- Keep the same meaning/concept
- Keep the same tone and energy
- Keep the EXACT same structure (same number of lines, same line breaks)
- If a line has quotes, your rewritten line should have quotes in the same spot
- If a line is short, keep it short. If it's long, keep it long.
- Make it sound natural and viral-worthy
- Just give me the rewritten text, nothing else

Original:
{text}"""

def main():
    if not API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Get video folder from command line
    if len(sys.argv) < 2:
        print("Usage: python extract_captions.py <video_folder>")
        print("Example: python extract_captions.py C:\\Users\\asus\\Desktop\\videos")
        sys.exit(1)

    video_folder = Path(sys.argv[1])
    if not video_folder.exists():
        print(f"Error: Folder not found: {video_folder}")
        sys.exit(1)

    # Find all MP4 files
    mp4_files = sorted(video_folder.glob('*.mp4'))
    if not mp4_files:
        print(f"No MP4 files found in {video_folder}")
        sys.exit(1)

    print(f"Found {len(mp4_files)} videos in {video_folder}", flush=True)

    # Create timestamped output folder
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    output_base = Path(__file__).parent / "extracted_captions"
    run_folder = output_base / f"run_{timestamp}"
    screenshots_folder = run_folder / "screenshots"
    screenshots_folder.mkdir(parents=True, exist_ok=True)

    output_txt = run_folder / "cap.txt"
    output_csv = run_folder / "cap.csv"

    print(f"Output folder: {run_folder}", flush=True)

    # Step 1: Extract screenshots from all videos
    print("\n--- Extracting screenshots ---", flush=True)
    screenshot_files = []
    for i, mp4_file in enumerate(mp4_files):
        print(f"[{i+1}/{len(mp4_files)}] {mp4_file.name}", flush=True)
        screenshot_path = screenshots_folder / f"{mp4_file.stem}.jpg"

        cmd = [
            "ffmpeg", "-i", str(mp4_file),
            "-ss", "00:00:02",
            "-vframes", "1",
            str(screenshot_path),
            "-y", "-loglevel", "error"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if screenshot_path.exists():
            screenshot_files.append(screenshot_path)
            print(f"    OK", flush=True)
        else:
            print(f"    FAILED: {result.stderr}", flush=True)

    print(f"\nExtracted {len(screenshot_files)} screenshots", flush=True)

    # Step 2: OCR and rewrite each screenshot
    print("\n--- Processing captions ---", flush=True)
    client = anthropic.Anthropic(api_key=API_KEY)
    results = []

    for i, img_file in enumerate(screenshot_files):
        print(f"[{i+1}/{len(screenshot_files)}] {img_file.name}", flush=True)

        try:
            # OCR: Extract text from image
            with open(img_file, 'rb') as image:
                image_data = base64.standard_b64encode(image.read()).decode('utf-8')

            message = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                        {"type": "text", "text": "Extract all the text visible in this image. Just give me the text, nothing else."}
                    ],
                }],
            )
            original_text = message.content[0].text.strip()
            print(f"    Extracted", flush=True)

            # Rewrite the caption
            rewrite_msg = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": REWRITE_PROMPT.format(text=original_text)
                }],
            )
            rewritten_text = rewrite_msg.content[0].text.strip()
            print(f"    Rewritten", flush=True)

            results.append((img_file.stem, original_text, rewritten_text))

        except Exception as e:
            results.append((img_file.stem, f"ERROR: {e}", ""))
            print(f"    ERROR: {e}", flush=True)

    # Write text file
    with open(output_txt, 'w', encoding='utf-8') as f:
        for filename, original, rewritten in results:
            f.write(f"{filename}\n")
            f.write(f"ORIGINAL:\n{original}\n")
            f.write(f"REWRITTEN:\n{rewritten}\n\n")

    # Write CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "original", "rewritten"])
        for filename, original, rewritten in results:
            writer.writerow([filename, original, rewritten])

    print(f"\nDone!", flush=True)
    print(f"Results: {run_folder}", flush=True)

if __name__ == "__main__":
    main()
