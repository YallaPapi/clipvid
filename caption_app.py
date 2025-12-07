import anthropic
import base64
import csv
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, simpledialog
from pathlib import Path
from datetime import datetime
import os
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


class CaptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Caption Extractor")
        self.root.geometry("600x550")

        self.video_folder = None
        self.output_folder = None
        self.running = False

        # Video folder selection
        frame_video = tk.Frame(root, pady=5)
        frame_video.pack(fill=tk.X, padx=10)

        self.btn_select_video = tk.Button(frame_video, text="Select Video Folder", command=self.select_video_folder, width=20)
        self.btn_select_video.pack(side=tk.LEFT)

        self.lbl_video = tk.Label(frame_video, text="No video folder selected", anchor="w")
        self.lbl_video.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Output folder selection
        frame_output = tk.Frame(root, pady=5)
        frame_output.pack(fill=tk.X, padx=10)

        self.btn_select_output = tk.Button(frame_output, text="Select Output Folder", command=self.select_output_folder, width=20)
        self.btn_select_output.pack(side=tk.LEFT)

        self.lbl_output = tk.Label(frame_output, text="No output folder selected", anchor="w")
        self.lbl_output.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Run button
        self.btn_run = tk.Button(root, text="Run", command=self.start_processing, width=20, height=2, state=tk.DISABLED)
        self.btn_run.pack(pady=10)

        # Progress label
        self.lbl_progress = tk.Label(root, text="", font=("Arial", 10, "bold"))
        self.lbl_progress.pack()

        # Log area
        self.log = scrolledtext.ScrolledText(root, height=20, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def select_video_folder(self):
        folder = filedialog.askdirectory(title="Select folder with MP4 videos")
        if folder:
            self.video_folder = Path(folder)
            mp4_count = len(list(self.video_folder.glob('*.mp4')))
            self.lbl_video.config(text=f"{folder} ({mp4_count} videos)")
            self.check_ready()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder = Path(folder)
            self.lbl_output.config(text=str(folder))
            self.check_ready()

    def check_ready(self):
        ready = (
            self.video_folder is not None
            and self.output_folder is not None
            and len(list(self.video_folder.glob('*.mp4'))) > 0
        )
        self.btn_run.config(state=tk.NORMAL if ready else tk.DISABLED)

    def log_msg(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def update_progress(self, text):
        self.lbl_progress.config(text=text)

    def start_processing(self):
        if self.running:
            return
        self.running = True
        self.btn_run.config(state=tk.DISABLED)
        self.btn_select_video.config(state=tk.DISABLED)
        self.btn_select_output.config(state=tk.DISABLED)
        self.log.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.process_videos, daemon=True)
        thread.start()

    def process_videos(self):
        try:
            mp4_files = sorted(self.video_folder.glob('*.mp4'))
            total = len(mp4_files)

            self.root.after(0, lambda: self.log_msg(f"Found {total} videos"))

            # Create timestamped run folder inside chosen output folder
            timestamp = datetime.now().strftime("%y%m%d_%H%M")
            run_folder = self.output_folder / f"run_{timestamp}"
            screenshots_folder = run_folder / "screenshots"
            screenshots_folder.mkdir(parents=True, exist_ok=True)

            self.root.after(0, lambda: self.log_msg(f"Output: {run_folder}\n"))

            # Step 1: Extract screenshots
            self.root.after(0, lambda: self.log_msg("--- Extracting screenshots ---"))
            screenshot_files = []

            for i, mp4_file in enumerate(mp4_files):
                self.root.after(0, lambda i=i, t=total: self.update_progress(f"Extracting screenshots: {i+1}/{t}"))
                self.root.after(0, lambda f=mp4_file.name: self.log_msg(f"[Screenshot] {f}"))

                screenshot_path = screenshots_folder / f"{mp4_file.stem}.jpg"
                cmd = [
                    "ffmpeg", "-i", str(mp4_file),
                    "-ss", "00:00:02",
                    "-vframes", "1",
                    str(screenshot_path),
                    "-y", "-loglevel", "error"
                ]
                subprocess.run(cmd, capture_output=True, text=True)

                if screenshot_path.exists():
                    screenshot_files.append(screenshot_path)

            self.root.after(0, lambda: self.log_msg(f"\nExtracted {len(screenshot_files)} screenshots\n"))

            # Step 2: OCR and rewrite
            self.root.after(0, lambda: self.log_msg("--- Processing captions ---"))
            client = anthropic.Anthropic(api_key=API_KEY)
            results = []

            for i, img_file in enumerate(screenshot_files):
                self.root.after(0, lambda i=i, t=len(screenshot_files): self.update_progress(f"Processing captions: {i+1}/{t}"))
                self.root.after(0, lambda f=img_file.name: self.log_msg(f"[{f}] Extracting..."))

                try:
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
                    self.root.after(0, lambda f=img_file.name: self.log_msg(f"[{f}] Rewriting..."))

                    rewrite_msg = client.messages.create(
                        model=MODEL,
                        max_tokens=1024,
                        messages=[{
                            "role": "user",
                            "content": REWRITE_PROMPT.format(text=original_text)
                        }],
                    )
                    rewritten_text = rewrite_msg.content[0].text.strip()
                    self.root.after(0, lambda f=img_file.name: self.log_msg(f"[{f}] Done"))

                    results.append((img_file.stem, original_text, rewritten_text))

                except Exception as e:
                    self.root.after(0, lambda e=e: self.log_msg(f"  ERROR: {e}"))
                    results.append((img_file.stem, f"ERROR: {e}", ""))

            # Save results
            output_txt = run_folder / "cap.txt"
            output_csv = run_folder / "cap.csv"

            with open(output_txt, 'w', encoding='utf-8') as f:
                for filename, original, rewritten in results:
                    f.write(f"{filename}\n")
                    f.write(f"ORIGINAL:\n{original}\n")
                    f.write(f"REWRITTEN:\n{rewritten}\n\n")

            with open(output_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "original", "rewritten"])
                for filename, original, rewritten in results:
                    writer.writerow([filename, original, rewritten])

            self.root.after(0, lambda: self.log_msg(f"\n--- Done! ---"))
            self.root.after(0, lambda: self.log_msg(f"Results saved to: {run_folder}"))
            self.root.after(0, lambda: self.update_progress("Complete!"))

        except Exception as e:
            self.root.after(0, lambda e=e: self.log_msg(f"Error: {e}"))
            self.root.after(0, lambda: self.update_progress("Error occurred"))

        finally:
            self.running = False
            self.root.after(0, lambda: self.btn_run.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_select_video.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_select_output.config(state=tk.NORMAL))


if __name__ == "__main__":
    global API_KEY
    if not API_KEY:
        root = tk.Tk()
        root.withdraw()
        API_KEY = simpledialog.askstring("API Key", "Enter your Anthropic API key:", show='*')
        if not API_KEY:
            exit()
        root.destroy()

    root = tk.Tk()
    app = CaptionApp(root)
    root.mainloop()
