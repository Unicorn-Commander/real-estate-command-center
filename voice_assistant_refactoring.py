# Revised Voice Assistant using QtMultimedia
from PySide6.QtMultimedia import QMediaRecorder, QAudioInput, QAudioSource, QMediaCaptureSession, QMediaFormat
from PySide6.QtCore import QUrl, QBuffer

class VoiceAssistant(QObject):
    # ... existing code ...

    def start_recording(self):
        self.recording = True
        self.audio_data = bytearray()
        
        # QtMultimedia setup
        self.format = QMediaFormat()
        self.format.setFileFormat(QMediaFormat.Wave)
        
        input_device = QMediaDevices.defaultAudioInput()
        if input_device.isNull():
            print("No audio input device available")
            return
            
        self.audio_source = QAudioSource(input_device)
        self.capture_session = QMediaCaptureSession()
        self.recorder = QMediaRecorder()
        self.capture_session.setAudioInput(self.audio_source)
        self.capture_session.setRecorder(self.recorder)
        self.recorder.setMediaFormat(self.format)
        
        # Create temp file
        self.temp_file = QTemporaryFile()
        self.temp_file.open()
        self.recorder.setOutputLocation(QUrl.fromLocalFile(self.temp_file.fileName()))
        self.recorder.record()
    
    def stop_recording(self):
        if self.recording:
            self.recorder.stop()
            self.recording = False
            self.temp_file.seek(0)
            self.audio_data = self.temp_file.readAll()
            asyncio.create_task(self.process_audio())