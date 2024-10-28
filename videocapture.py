import sys
from threading import Thread
from queue import Queue


class Video_capture_thread(Thread):

    def __init__(self, *args, **kwargs):
        super(Video_capture_thread, self).__init__(*args, **kwargs)
        self.queue = Queue()
        self.capture = None
        self.is_transcribe = False

    def run(self):
        if self.is_transcribe:
            return
        while True:
            ret, frame = self.capture.read()
            if not ret:
                continue
            self.queue.put(frame)

    def get_frame(self):
        if self.is_transcribe:
            ret, frame = self.capture.read()
            if not ret:
                print("The video is transcribed.")
                self.capture.release()
                sys.exit(0)
            return frame
        else:
            return self.queue.get()
