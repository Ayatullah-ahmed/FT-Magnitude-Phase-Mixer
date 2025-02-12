import numpy as np
import cv2  # OpenCV for image processing
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from Convert import Convert



class FFTHandler:
    def __init__(self, image_handler,ui,image_mixing):
        self.image_handler = image_handler
        self.ui = ui
        self.image_mixing = image_mixing
        self.convert=Convert()
        #private attribute
        # Initialize the region selector size (defaults to cover the whole image)
        self._selector_region = [0, 0, 50, 50]  # [x, y, width, height]
        self._FT_images=[None]*4
        self._FT_image_labels = [
            self.ui.FT_components_1,
            self.ui.FT_components_2,
            self.ui.FT_components_3,
            self.ui.FT_components_4
        ]
        self._comp_selection = [
            self.ui.comp_selection_1,
            self.ui.comp_selection_2,
            self.ui.comp_selection_3,
            self.ui.comp_selection_4
        ]

        # Getter for _selector_region

    @property
    def selector_region(self):
        return self._selector_region

    # Setter for _selector_region
    @selector_region.setter
    def selector_region(self, value):
        if isinstance(value, list) and len(value) == 4:
            self._selector_region = value
        else:
            raise ValueError("selector_region must be a list of four elements.")

    # Getter for _FT_images
    @property
    def FT_images(self):
        return self._FT_images

    # Setter for _FT_images
    @FT_images.setter
    def FT_images(self, value):
        if isinstance(value, list) and len(value) == 4:
            self._FT_images = value
        else:
            raise ValueError("FT_images must be a list of four elements.")

    # Getter for _FT_image_labels
    @property
    def FT_image_labels(self):
        return self._FT_image_labels

    # Getter for _comp_selection
    @property
    def comp_selection(self):
        return self._comp_selection

    def __draw_selector_on_ft_image(self, index):
        """Draw a semi-transparent rectangle selector on the FT image."""

        if self.FT_images[index] is not None :
            # Create a copy of the FT image to draw the rectangle
            ft_image = self.FT_images[index].copy()

            # Get selector position and size
            x, y, w, h = self.selector_region
            if self.ui.none_region.isChecked():
                x, y, w, h = [0, 0, 0, 0]
            # Ensure the selector fits within the image bounds
            x = max(0, min(x, ft_image.shape[1] - w))
            y = max(0, min(y, ft_image.shape[0] - h))

            # Normalize the image for display (scale to 0-255 if needed)
            if ft_image.dtype != np.uint8:
                ft_image = cv2.normalize(ft_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

            # Convert grayscale to BGR for drawing a colored rectangle
            if len(ft_image.shape) == 2:  # Grayscale
                ft_image = cv2.cvtColor(ft_image, cv2.COLOR_GRAY2BGR)

            # Create an overlay to blend with the original image
            overlay = ft_image.copy()
            alpha = 0.4  # Transparency factor (0.0 = transparent, 1.0 = opaque)

            # Draw a solid rectangle on the overlay
            color = (0, 255, 0)  # Green color for the rectangle
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)  # -1 fills the rectangle

            # Blend the overlay with the original image
            cv2.addWeighted(overlay, alpha, ft_image, 1 - alpha, 0, ft_image)

            # Draw the rectangle's border for visibility (fully opaque)
            border_color = (0, 255, 0)  # Green border
            thickness = 2  # Thickness of the border
            cv2.rectangle(ft_image, (x, y), (x + w, y + h), border_color, thickness)

            # Convert to QPixmap and display
            qt_image = self.convert.convert_cv_to_qt(ft_image)
            if qt_image is not None:
                pixmap = QPixmap.fromImage(qt_image)
                self.FT_image_labels[index].setPixmap(
                    pixmap.scaled(self.FT_image_labels[index].size(), Qt.KeepAspectRatio)
                )

    def update_display(self,images,min_height,min_width,weights):
        for i, combo in enumerate(self.comp_selection):
            selected = combo.currentText()
            if images[i] is not None:
                if selected == "FT Magnitude":
                    self.__display_ft_magnitude(i,images)
                elif selected == "FT Phase":
                    self.__display_ft_phase(i,images)
                elif selected == "FT Real":
                    self.__display_ft_real(i,images)
                elif selected == "FT Imaginary":
                    self.__display_ft_imaginary(i,images)
        self.image_mixing.mix_and_display(self.selector_region,min_height,min_width,images,weights)  # Trigger mixing and display after component update

    def __display_ft_magnitude(self, index,images):
        ft_image = np.fft.fft2(images[index])  # Compute Fourier Transform
        magnitude = np.abs(np.fft.fftshift(ft_image))  # Shift low frequencies to center
        magnitude = np.log1p(magnitude)  # Apply log scaling
        magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)  # Normalize to [0, 255]

        self.FT_images[index] = magnitude
        self.__display_FT_images(index)

    def __display_ft_phase(self, index,images):
        ft_image = np.fft.fft2(images[index])  # Compute Fourier Transform
        phase = np.angle(np.fft.fftshift(ft_image))  # Compute phase and shift
        phase_scaled = (phase + np.pi) / (2 * np.pi) * 255  # Scale phase to [0, 255]
        phase_colored = phase_scaled.astype(np.uint8)
        self.FT_images[index] = phase_colored
        self.__display_FT_images(index)

    def __display_ft_real(self, index,images):
        ft_image = np.fft.fft2(images[index])  # Compute Fourier Transform
        real = np.real(np.fft.fftshift(ft_image))  # Compute real part and shift
        real_log = np.log1p(np.abs(real))  # Apply logarithmic scaling
        real_normalized = cv2.normalize(real_log, None, 0, 255, cv2.NORM_MINMAX).astype(
            np.uint8)  # Normalize for display
        self.FT_images[index] = real_normalized
        self.__display_FT_images(index)

    def __display_ft_imaginary(self, index,images):
        ft_image = np.fft.fft2(images[index])  # Compute Fourier Transform
        imaginary = np.imag(np.fft.fftshift(ft_image))  # Compute imaginary part and shift
        imaginary_log = np.log1p(np.abs(imaginary))  # Apply logarithmic scaling
        imaginary_normalized = cv2.normalize(imaginary_log, None, 0, 255, cv2.NORM_MINMAX).astype(
            np.uint8)  # Normalize for display
        self.FT_images[index] = imaginary_normalized
        self.__display_FT_images(index)

    def __display_FT_images(self, index):

        if self.FT_images[index] is not None:
            qt_image = self.convert.convert_cv_to_qt(self.FT_images[index])
            if qt_image is not None:
                pixmap = QPixmap.fromImage(qt_image)
                label = self.FT_image_labels[index]
                label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio))
            self.__draw_selector_on_ft_image(index)
    def update_selectors(self, value ,min_height,min_width,images,weights,main_window):
        """Update selectors on all FT images based on the slider value."""
        rect_size = max(50, value)  # Minimum size is 50x50
        self.selector_region[2] = rect_size  # Width
        self.selector_region[3] = rect_size  # Height

        for idx, image in enumerate(self.FT_images):
            if image is not None:
                # Center the selector on the image
                height, width = image.shape[:2]
                x = (width - rect_size) // 2
                y = (height - rect_size) // 2
                self.selector_region[0] = x
                self.selector_region[1] = y

                # Redraw the FT image with the selector
                self.__draw_selector_on_ft_image(idx)
        main_window.start_thread()
    def reset(self,main_window):
        for i in range(4):
            self.__draw_selector_on_ft_image(i)
        main_window.start_thread()