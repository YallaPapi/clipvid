# Caption Extractor

A desktop app that extracts text from video screenshots using Claude AI vision, then rewrites the captions while preserving their original structure and tone.

## What it does

1. Takes a folder of MP4 videos
2. Extracts a screenshot from each video (at 2 seconds)
3. Uses Claude AI to OCR the text visible in each screenshot
4. Rewrites each caption with the same meaning, tone, and structure
5. Saves both original and rewritten captions to TXT and CSV files

## Requirements

- Python 3.10+
- FFmpeg (must be in PATH)
- Anthropic API key

## Installation

```bash
pip install anthropic
```

## Usage

### GUI App (Recommended)

Run the desktop app:
```bash
python caption_app.py
```

Or use the pre-built executable:
```
dist/CaptionExtractor.exe
```

1. Click "Select Video Folder" - choose folder with MP4 files
2. Click "Select Output Folder" - choose where to save results
3. Click "Run"

### Command Line

```bash
python extract_captions.py "C:\path\to\videos"
```

## Output

Each run creates a timestamped folder:
```
output_folder/
└── run_251207_1630/
    ├── screenshots/
    │   ├── video1.jpg
    │   ├── video2.jpg
    │   └── ...
    ├── cap.txt
    └── cap.csv
```

- `screenshots/` - Extracted frames from each video
- `cap.txt` - Human-readable text file with original and rewritten captions
- `cap.csv` - Spreadsheet format with columns: filename, original, rewritten

## Configuration

Set your API key as an environment variable:
```bash
set ANTHROPIC_API_KEY=your-api-key-here
```

Or on Mac/Linux:
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

The GUI app will prompt for the API key if not set.

## Building the EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "CaptionExtractor" caption_app.py
```

The executable will be in the `dist/` folder.

## Cost

Uses Claude Sonnet 4.5 for both OCR and rewriting. Approximate cost: $2-4 per 100 videos.
