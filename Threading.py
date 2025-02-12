import threading
import time
import logging

# Configure logging to capture all log levels
logging.basicConfig(filemode="a", filename="our_log.log",
                    format="(%(asctime)s) | %(name)s| %(levelname)s | => %(message)s", level=logging.INFO)


class WorkerSignals:
    canceled = threading.Event()


class WorkerThread(threading.Thread, ):
    def __init__(self, seconds, signals, main_window):
        super().__init__()
        self.seconds = seconds
        self.signals = signals
        self.main_window = main_window
        # Initialize progress value
        self.progress_value = 0

    def run(self):
        for i in range(self.seconds):
            time.sleep(1)
            self.update_progress()
            if self.signals.canceled.is_set():
                logging.info(
                    f'Thread canceled - Remaining time: {self.seconds - i - 1} seconds')
                return
        logging.info('Thread completed')

    def cancel(self):
        self.signals.canceled.set()
        self.join()

    def update_progress(self):
        # This function can be called to update the progress bar manually
        if self.progress_value == 0:
            self.main_window.collect_chunks()

        self.progress_value += 20
        self.main_window.ui.progressBar.setValue(self.progress_value)

        if self.progress_value == 100:
            self.main_window.image_mixing.mix_and_display(self.main_window.fft_handler.selector_region,self.main_window.image_handler.min_height,self.main_window.image_handler.min_width,self.main_window.images,self.main_window.weights)