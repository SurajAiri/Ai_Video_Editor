import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QScrollArea, 
                              QComboBox, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPalette, QFont

class TranscriptTile(QFrame):
    def __init__(self, text, start_time, end_time, parent=None):
        super().__init__(parent)
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.selected = False
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("background-color: white; border-radius: 10px; padding: 10px;")
        
        layout = QVBoxLayout(self)
        
        # Text label
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.text_label)
        
        # Time label
        time_label = QLabel(f"{start_time:.2f} - {end_time:.2f}")
        time_label.setAlignment(Qt.AlignRight)
        time_label.setStyleSheet("color: gray;")
        layout.addWidget(time_label)
        
        self.setLayout(layout)
        
    def mousePressEvent(self, event):
        self.selected = not self.selected
        if self.selected:
            self.setStyleSheet("background-color: #e6f2ff; border-radius: 10px; padding: 10px;")
        else:
            self.setStyleSheet("background-color: white; border-radius: 10px; padding: 10px;")
        super().mousePressEvent(event)

class TranscriptEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcript Editor")
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Top toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        
        load_button = QPushButton("Load Transcript")
        exit_button = QPushButton("Exit Edit Mode")
        exit_button.setStyleSheet("background-color: #0078d7; color: white;")
        
        # Invalid type section
        invalid_label = QLabel("Invalid Type:")
        invalid_combo = QComboBox()
        invalid_combo.addItem("repetition")
        invalid_combo.addItem("stuttering")
        invalid_combo.addItem("filler")
        
        add_invalid_button = QPushButton("Add Invalid")
        save_button = QPushButton("Save Checkpoint")
        
        toolbar_layout.addWidget(load_button)
        toolbar_layout.addWidget(exit_button)
        toolbar_layout.addSpacing(20)
        toolbar_layout.addWidget(invalid_label)
        toolbar_layout.addWidget(invalid_combo)
        toolbar_layout.addWidget(add_invalid_button)
        toolbar_layout.addWidget(save_button)
        
        main_layout.addWidget(toolbar)
        
        # Transcript area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: #f0f0f0;")
        
        # Container for transcript tiles
        self.transcript_container = QWidget()
        self.transcript_layout = QVBoxLayout(self.transcript_container)
        self.transcript_layout.setSpacing(10)
        self.transcript_layout.setContentsMargins(20, 20, 20, 20)
        self.transcript_layout.addStretch()
        
        scroll_area.setWidget(self.transcript_container)
        main_layout.addWidget(scroll_area)
        
        # Status bar
        status_bar = QLabel("Click a word to select it. Click an additional word to select a range. Click selected word to deselect.")
        status_bar.setStyleSheet("background-color: #333; color: white; padding: 10px;")
        main_layout.addWidget(status_bar)
        
        self.setCentralWidget(central_widget)
        
        # Connect signals
        load_button.clicked.connect(self.load_transcript)
        
    def load_transcript(self):
        # Example transcript data (in real app, you would load from file)
        transcript_json = """
        {
            "data": [
                {
                    "word": "you",
                    "start": 0.48,
                    "end": 0.71999997
                },
                {
                    "word": "know",
                    "start": 0.71999997,
                    "end": 0.96
                },
                {
                    "word": "what",
                    "start": 0.96,
                    "end": 1.2
                },
                {
                    "word": "I",
                    "start": 1.2,
                    "end": 1.32
                },
                {
                    "word": "mean",
                    "start": 1.32,
                    "end": 1.56
                },
                {
                    "word": "it's",
                    "start": 1.8,
                    "end": 2.04
                },
                {
                    "word": "like",
                    "start": 2.04,
                    "end": 2.28
                },
                {
                    "word": "uh",
                    "start": 2.28,
                    "end": 2.4
                },
                {
                    "word": "and",
                    "start": 2.7,
                    "end": 2.94
                },
                {
                    "word": "then",
                    "start": 2.94,
                    "end": 3.18
                },
                {
                    "word": "I",
                    "start": 3.18,
                    "end": 3.3
                },
                {
                    "word": "was",
                    "start": 3.3,
                    "end": 3.54
                },
                {
                    "word": "going",
                    "start": 3.54,
                    "end": 3.78
                },
                {
                    "word": "to",
                    "start": 3.78,
                    "end": 3.9
                },
                {
                    "word": "say",
                    "start": 3.9,
                    "end": 3.96
                }
            ]
        }
        """
        
        # Clear existing transcript
        for i in reversed(range(self.transcript_layout.count())):
            widget = self.transcript_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Group words into segments based on timing gaps
        transcript_data = json.loads(transcript_json)["data"]
        segments = []
        current_segment = []
        
        for i, word_data in enumerate(transcript_data):
            current_segment.append(word_data)
            
            # If this is the last word or there's a time gap to the next word
            if i == len(transcript_data) - 1 or transcript_data[i+1]["start"] - word_data["end"] > 0.2:
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
        
        # Create tiles for each segment
        for segment in segments:
            segment_text = " ".join([word["word"] for word in segment])
            start_time = segment[0]["start"]
            end_time = segment[-1]["end"]
            
            tile = TranscriptTile(segment_text, start_time, end_time)
            self.transcript_layout.insertWidget(self.transcript_layout.count()-1, tile)
        
        self.transcript_layout.addStretch()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = TranscriptEditor()
    window.show()
    
    sys.exit(app.exec())