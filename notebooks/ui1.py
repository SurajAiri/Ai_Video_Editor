import sys
import json
import os
from datetime import timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, 
                            QTextEdit, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


class TranscriptEditor(QTextEdit):
    selectionChanged = pyqtSignal(float, float, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.transcript_data = []
        self.current_selection = None
        self.start_word = None
        self.end_word = None
        self.setMouseTracking(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
    def set_transcript(self, transcript_data):
        """Set transcript data and display it"""
        self.transcript_data = transcript_data
        self.clear()
        
        # Format for word display
        text = ""
        for i, word in enumerate(transcript_data):
            text += word['word'] + " "
            
        self.setPlainText(text)
    
    def mousePressEvent(self, event):
        """Handle mouse press to start selection or clear selection if clicking on already selected word"""
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        word_position = cursor.position() - cursor.selectionStart()
        selected_text = cursor.selectedText()
        
        # Find the corresponding word in transcript_data
        current_pos = 0
        selected_word_index = -1
        
        for i, word in enumerate(self.transcript_data):
            word_length = len(word['word'])
            if current_pos <= cursor.selectionStart() < current_pos + word_length + 1:
                selected_word_index = i
                break
            current_pos += word_length + 1
        
        if selected_word_index >= 0:
            if self.start_word is None:
                # Starting a new selection
                self.start_word = selected_word_index
                self.highlightWord(selected_word_index)
            elif self.start_word == selected_word_index and self.end_word is None:
                # Clicking on the same word - deselect
                self.clearSelection()
            elif self.end_word is not None:
                # Reset and start a new selection
                self.clearSelection()
                self.start_word = selected_word_index
                self.highlightWord(selected_word_index)
            
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end selection"""
        if self.start_word is not None:
            cursor = self.cursorForPosition(event.pos())
            cursor.select(QTextCursor.WordUnderCursor)
            
            # Find the corresponding word in transcript_data
            current_pos = 0
            selected_word_index = -1
            
            for i, word in enumerate(self.transcript_data):
                word_length = len(word['word'])
                if current_pos <= cursor.selectionStart() < current_pos + word_length + 1:
                    selected_word_index = i
                    break
                current_pos += word_length + 1
            
            if selected_word_index >= 0 and selected_word_index != self.start_word:
                self.end_word = selected_word_index
                
                # Make sure start is less than end
                if self.start_word > self.end_word:
                    self.start_word, self.end_word = self.end_word, self.start_word
                
                self.highlightSelection(self.start_word, self.end_word)
                
                # Emit the selection
                start_time = float(self.transcript_data[self.start_word]['start_time'])
                end_time = float(self.transcript_data[self.end_word]['end_time'])
                text = ' '.join([word['word'] for word in self.transcript_data[self.start_word:self.end_word+1]])
                self.selectionChanged.emit(start_time, end_time, text)
        
        super().mouseReleaseEvent(event)
    
    def highlightWord(self, word_index):
        """Highlight a single word"""
        self.clearSelection()
        
        cursor = QTextCursor(self.document())
        current_pos = 0
        
        for i, word in enumerate(self.transcript_data):
            word_length = len(word['word'])
            if i == word_index:
                cursor.setPosition(current_pos)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, word_length)
                
                format = QTextCharFormat()
                format.setBackground(QColor(255, 255, 0, 100))  # Light yellow
                cursor.mergeCharFormat(format)
                break
                
            current_pos += word_length + 1  # Add 1 for space
    
    def highlightSelection(self, start_index, end_index):
        """Highlight a range of words"""
        self.clearSelection()
        
        cursor = QTextCursor(self.document())
        current_pos = 0
        start_pos = 0
        end_pos = 0
        
        for i, word in enumerate(self.transcript_data):
            word_length = len(word['word'])
            
            if i == start_index:
                start_pos = current_pos
            
            if i == end_index:
                end_pos = current_pos + word_length
                break
                
            current_pos += word_length + 1  # Add 1 for space
        
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
        
        format = QTextCharFormat()
        format.setBackground(QColor(255, 255, 0, 100))  # Light yellow
        cursor.mergeCharFormat(format)
    
    def clearSelection(self):
        """Clear all highlighting"""
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.Document)
        
        format = QTextCharFormat()
        format.setBackground(Qt.transparent)
        cursor.mergeCharFormat(format)
        
        self.start_word = None
        self.end_word = None


class SegmentItem(QWidget):
    accepted = pyqtSignal(dict)
    rejected = pyqtSignal(dict)
    play_segment = pyqtSignal(float, float)
    
    def __init__(self, segment_data, parent=None):
        super().__init__(parent)
        self.segment_data = segment_data
        
        layout = QHBoxLayout()
        
        # Format display text
        time_range = f"{float(segment_data['start_time']):.2f}s - {float(segment_data['end_time']):.2f}s"
        segment_type = segment_data['type']
        is_entire = "entire segment" if segment_data.get('is_entire', False) else "partial segment" 
        
        info_label = QLabel(f"{time_range} | {segment_type} | {is_entire}")
        play_button = QPushButton("Play")
        accept_button = QPushButton("Accept")
        reject_button = QPushButton("Reject")
        
        layout.addWidget(info_label)
        layout.addWidget(play_button)
        layout.addWidget(accept_button)
        layout.addWidget(reject_button)
        
        self.setLayout(layout)
        
        # Connect signals
        play_button.clicked.connect(self.play_clicked)
        accept_button.clicked.connect(self.accept_clicked)
        reject_button.clicked.connect(self.reject_clicked)
    
    def play_clicked(self):
        start_time = float(self.segment_data['start_time'])
        end_time = float(self.segment_data['end_time'])
        self.play_segment.emit(start_time, end_time)
    
    def accept_clicked(self):
        self.accepted.emit(self.segment_data)
    
    def reject_clicked(self):
        self.rejected.emit(self.segment_data)


class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editing Automation")
        self.setGeometry(100, 100, 1200, 800)
        
        self.segments = []
        self.transcript = []
        self.accepted_segments = []
        self.rejected_segments = []
        self.current_video = ""
        
        self.init_ui()
    
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Top controls
        top_controls = QHBoxLayout()
        self.load_video_button = QPushButton("Load Video")
        self.load_segments_button = QPushButton("Load Segments")
        self.process_button = QPushButton("Process Video")
        self.save_button = QPushButton("Save Results")
        
        top_controls.addWidget(self.load_video_button)
        top_controls.addWidget(self.load_segments_button)
        top_controls.addWidget(self.process_button)
        top_controls.addWidget(self.save_button)
        
        main_layout.addLayout(top_controls)
        
        # Splitter for video and content
        splitter = QSplitter(Qt.Vertical)
        
        # Video player
        video_widget = QWidget()
        video_layout = QVBoxLayout()
        
        self.video_player = QMediaPlayer()
        self.video_display = QVideoWidget()
        self.video_player.setVideoOutput(self.video_display)
        
        video_controls = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.position_label = QLabel("Position: 0:00")
        
        video_controls.addWidget(self.play_button)
        video_controls.addWidget(self.pause_button)
        video_controls.addWidget(self.position_label)
        
        video_layout.addWidget(self.video_display)
        video_layout.addLayout(video_controls)
        video_widget.setLayout(video_layout)
        
        # Content area
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        
        # Left side - segments list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        segments_label = QLabel("Detected Segments")
        segments_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.segments_list = QListWidget()
        
        left_layout.addWidget(segments_label)
        left_layout.addWidget(self.segments_list)
        left_panel.setLayout(left_layout)
        
        # Right side - transcript editor
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        transcript_label = QLabel("Transcript")
        transcript_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.transcript_editor = TranscriptEditor()
        
        right_layout.addWidget(transcript_label)
        right_layout.addWidget(self.transcript_editor)
        right_panel.setLayout(right_layout)
        
        # Add panels to content layout
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel, 2)
        content_widget.setLayout(content_layout)
        
        # Add widgets to splitter
        splitter.addWidget(video_widget)
        splitter.addWidget(content_widget)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Connect signals
        self.load_video_button.clicked.connect(self.load_video)
        self.load_segments_button.clicked.connect(self.load_segments)
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.process_button.clicked.connect(self.process_video)
        self.save_button.clicked.connect(self.save_results)
        self.transcript_editor.selectionChanged.connect(self.on_transcript_selection)
        self.video_player.positionChanged.connect(self.update_position)
    
    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", 
                                                "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)")
        
        if file_path:
            self.current_video = file_path
            self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.status_bar.showMessage(f"Loaded video: {os.path.basename(file_path)}")
            
            # For a real application, you would also load/generate transcript here
            # This is a placeholder for demonstration
            self.load_placeholder_transcript()
    
    def load_segments(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Segments JSON", "", 
                                                "JSON Files (*.json);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if 'data' in data:
                    self.segments = data['data']
                    self.update_segments_list()
                    self.status_bar.showMessage(f"Loaded {len(self.segments)} segments")
                else:
                    self.status_bar.showMessage("Invalid JSON format: missing 'data' field")
            except Exception as e:
                self.status_bar.showMessage(f"Error loading segments: {str(e)}")
    
    def load_placeholder_transcript(self):
        # In a real application, this would come from an API or file
        # This is just a placeholder for demonstration
        sample_transcript = [
            {"word": "Hello", "start_time": "0.10", "end_time": "0.45"},
            {"word": "and", "start_time": "0.48", "end_time": "0.60"},
            {"word": "welcome", "start_time": "0.62", "end_time": "0.95"},
            {"word": "to", "start_time": "0.98", "end_time": "1.05"},
            {"word": "this", "start_time": "1.08", "end_time": "1.25"},
            {"word": "video", "start_time": "1.28", "end_time": "1.60"},
            {"word": "where", "start_time": "1.65", "end_time": "1.85"},
            {"word": "we", "start_time": "1.88", "end_time": "2.00"},
            {"word": "will", "start_time": "2.02", "end_time": "2.15"},
            {"word": "discuss", "start_time": "2.18", "end_time": "2.55"},
            {"word": "um", "start_time": "2.60", "end_time": "2.85"},
            {"word": "the", "start_time": "2.90", "end_time": "3.00"},
            {"word": "topic", "start_time": "3.05", "end_time": "3.30"},
            {"word": "of", "start_time": "3.33", "end_time": "3.45"},
            {"word": "video", "start_time": "3.50", "end_time": "3.75"},
            {"word": "editing", "start_time": "3.78", "end_time": "4.10"},
            {"word": "automation", "start_time": "4.15", "end_time": "4.80"}
        ]
        
        self.transcript = sample_transcript
        self.transcript_editor.set_transcript(sample_transcript)
        self.status_bar.showMessage("Loaded transcript")
    
    def update_segments_list(self):
        self.segments_list.clear()
        
        for segment in self.segments:
            item = QListWidgetItem()
            segment_widget = SegmentItem(segment)
            item.setSizeHint(segment_widget.sizeHint())
            
            self.segments_list.addItem(item)
            self.segments_list.setItemWidget(item, segment_widget)
            
            # Connect signals
            segment_widget.play_segment.connect(self.play_segment)
            segment_widget.accepted.connect(self.accept_segment)
            segment_widget.rejected.connect(self.reject_segment)
    
    def play_video(self):
        self.video_player.play()
    
    def pause_video(self):
        self.video_player.pause()
    
    def update_position(self, position):
        seconds = position // 1000
        minutes = seconds // 60
        seconds %= 60
        self.position_label.setText(f"Position: {minutes}:{seconds:02d}")
    
    def play_segment(self, start_time, end_time):
        # Convert to milliseconds for the media player
        start_ms = int(start_time * 1000)
        
        # Set position and play
        self.video_player.setPosition(start_ms)
        self.video_player.play()
        
        # In a complete application, you would also implement stopping at end_time
        # This could be done with a QTimer
    
    def on_transcript_selection(self, start_time, end_time, text):
        self.status_bar.showMessage(f"Selected: {start_time:.2f}s - {end_time:.2f}s | '{text}'")
        
        # Create a new segment from the selection
        new_segment = {
            "start_time": f"{start_time:.2f}",
            "end_time": f"{end_time:.2f}",
            "type": "manual",
            "is_entire": False
        }
        
        # Add to segments and update list
        self.segments.append(new_segment)
        self.update_segments_list()
    
    def accept_segment(self, segment):
        self.accepted_segments.append(segment)
        
        # Remove from main list
        for i, seg in enumerate(self.segments):
            if (seg['start_time'] == segment['start_time'] and 
                seg['end_time'] == segment['end_time']):
                self.segments.pop(i)
                break
        
        self.update_segments_list()
        self.status_bar.showMessage(f"Segment accepted. {len(self.accepted_segments)} segments accepted.")
    
    def reject_segment(self, segment):
        self.rejected_segments.append(segment)
        
        # Remove from main list
        for i, seg in enumerate(self.segments):
            if (seg['start_time'] == segment['start_time'] and 
                seg['end_time'] == segment['end_time']):
                self.segments.pop(i)
                break
        
        self.update_segments_list()
        self.status_bar.showMessage(f"Segment rejected. {len(self.rejected_segments)} segments rejected.")
    
    def process_video(self):
        # This would typically call your Python processing logic
        self.status_bar.showMessage("Processing video... (This is a placeholder)")
        
        # For demonstration, add some example segments
        example_segments = [
            {
                "start_time": "0.48",
                "end_time": "2.40",
                "type": "repetition",
                "is_entire": True
            },
            {
                "start_time": "2.60",
                "end_time": "2.85",
                "type": "filler_words",
                "is_entire": True
            },
            {
                "start_time": "5.20",
                "end_time": "7.80",
                "type": "silence",
                "is_entire": True
            }
        ]
        
        self.segments = example_segments
        self.update_segments_list()
        self.status_bar.showMessage(f"Processing complete. Found {len(self.segments)} segments to review.")
    
    def save_results(self):
        if not self.accepted_segments:
            self.status_bar.showMessage("No segments to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Results", "", 
                                                  "JSON Files (*.json);;All Files (*)")
        
        if file_path:
            try:
                result = {
                    "data": self.accepted_segments
                }
                
                with open(file_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                self.status_bar.showMessage(f"Saved {len(self.accepted_segments)} segments to {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Error saving results: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoEditor()
    window.show()
    sys.exit(app.exec_())