Collecting workspace information# AI Video Editor

A tool for automatically cleaning up video content using AI-powered transcription and analysis.

## Overview

AI Video Editor intelligently processes video files to create polished final videos by:

1. Transcribing audio using either local (Whisper) or cloud-based (Deepgram) services
2. Analyzing transcripts to identify problematic segments:
   - Filler words ("um", "uh", "like", etc.)
   - Long pauses
   - Repeated sentences
3. Offering both automated cleanup and manual review options
4. Generating the final edited video with unwanted segments removed

## Features

- **Multiple Transcription Options**:
  - [Whisper](https://github.com/openai/whisper) (offline, local processing)
  - [Deepgram](https://deepgram.com/) (online, cloud-based)
  
- **Intelligent Analysis**:
  - Filler word detection
  - Pause detection
  - Repetition identification
  
- **Flexible Editing Workflow**:
  - Fully automated editing
  - Manual review and approval process
  - Control over edited content

- **Video Sequencing**:
  - Reorder multiple video clips
  - Combine clips into a polished final product

## Getting Started

### Prerequisites

- Python 3.12
- uv (package manager)

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ai_video_editor
```

2. Set up the Python environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Configure API keys (for Deepgram):
   - Create a .env file in the project root
   - Add your Deepgram API key: `DEEPGRAM_API_KEY=your_key_here`

## Usage

The application provides both a command-line interface and a graphical user interface:

1. Select video file(s) to process
2. Choose transcription method (Whisper or Deepgram)
3. Review and customize analysis settings
4. Select editing mode (automatic or manual review)
5. Generate the final edited video

### Command Line Example
```bash
python main.py --input video.mp4 --transcriber whisper --automatic
```

## Project Structure

```
├── LICENSE               <- MIT License
├── README.md             <- Project documentation
├── pyproject.toml        <- Python project configuration
├── main.py               <- Main entry point
├── app.py                <- GUI application
├── artifacts/            <- Sample media files
├── notebooks/            <- Development notebooks
└── src/                  <- Source code modules
    ├── transcribe/       <- Transcription implementation
    └── ui/               <- User interface components
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Suraj Airi - surajairi.ml@gmail.com