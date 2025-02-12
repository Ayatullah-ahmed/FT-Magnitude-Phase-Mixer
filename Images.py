import cv2
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from Convert import Convert


class ImageHandler:
    def __init__(self, ui):
        self.ui = ui
        self.convert = Convert()
        #private attribute
        self._brightness = [0] * 4
        self._contrast = [1.0] * 4
        self._min_width = None
        self._min_height = None
        # Brightness and contrast settings for each image
        self._brightness = [0] * 4
        self._contrast = [1.0] * 4
        self._image_labels = [
            self.ui.input_image_1,
            self.ui.input_image_2,
            self.ui.input_image_3,
            self.ui.input_image_4
        ]

    # Getter and Setter for _brightness
    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        if isinstance(value, list) and len(value) == 4:
            self._brightness = value
        else:
            raise ValueError("Brightness must be a list of four elements.")

    # Getter and Setter for _contrast
    @property
    def contrast(self):
        return self._contrast

    @contrast.setter
    def contrast(self, value):
        if isinstance(value, list) and len(value) == 4:
            self._contrast = value
        else:
            raise ValueError("Contrast must be a list of four elements.")

    # Getter and Setter for _min_width
    @property
    def min_width(self):
        return self._min_width

    @min_width.setter
    def min_width(self, value):
        if isinstance(value, (int, float)) or value is None:
            self._min_width = value
        else:
            raise ValueError("min_width must be an integer, float, or None.")

    # Getter and Setter for _min_height
    @property
    def min_height(self):
        return self._min_height

    @min_height.setter
    def min_height(self, value):
        if isinstance(value, (int, float)) or value is None:
            self._min_height = value
        else:
            raise ValueError("min_height must be an integer, float, or None.")

    # Getter for _image_labels
    @property
    def image_labels(self):
        return self._image_labels

    def __adjust_brightness_contrast(self, image, index):
        """Adjust brightness and contrast of the image."""
        new_image = cv2.convertScaleAbs(image, alpha=self.contrast[index], beta=self.brightness[index])
        return new_image


    def display_images(self,images):
        self.min_height = min(image.shape[0] for image in images if image is not None)
        self.min_width = min(image.shape[1] for image in images if image is not None)

        for idx, image in enumerate(images):
            if image is not None:
                adjusted_image = self.__adjust_brightness_contrast(image, idx)
                resized_image = cv2.resize(adjusted_image, (self.min_width, self.min_height))
                qt_image = self.convert.convert_cv_to_qt(resized_image)
                if qt_image is not None:
                    pixmap = QPixmap.fromImage(qt_image)
                    label = self.image_labels[idx]
                    # label.setGeometry(QtCore.QRect(14, 14, min_width, min_height))

                    label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio))
