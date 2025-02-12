from PyQt5.QtGui import QImage

class Convert:
    def __init__(self):
        pass
    def convert_cv_to_qt(self, cv_image):
        if cv_image.ndim == 2:  # Grayscale image
            height, width = cv_image.shape
            bytes_per_line = width
            return QImage(cv_image.data.tobytes(), width, height, bytes_per_line, QImage.Format_Grayscale8)
        elif cv_image.ndim == 3 and cv_image.shape[2] == 3:  # Color image (RGB)
            height, width, channel = cv_image.shape
            bytes_per_line = channel * width
            return QImage(cv_image.data.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
        else:
            print("Error: Unsupported image format.")
            return None
