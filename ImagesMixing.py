import cv2  # OpenCV for image processing
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import numpy as np
from PyQt5.QtCore import pyqtSlot
from Convert import Convert


class ImagesMixing:
    def __init__(self,ui):
        self.ui = ui
        self.convert = Convert()
        #private attributes
        self._region_mode = "none"  # Default region mode
        self._comp_selection = [
            self.ui.comp_selection_1,
            self.ui.comp_selection_2,
            self.ui.comp_selection_3,
            self.ui.comp_selection_4
        ]
        self._output_labels = [
            self.ui.output_image_1,
            self.ui.output_image_2
        ]
        self.chunks = {str(i): np.array([]) for i in range(4)}  # Initialize chunks dictionary

    # Getter and Setter for _region_mode
    @property
    def region_mode(self):
        return self._region_mode

    @region_mode.setter
    def region_mode(self, value):
        if value in ["none", "inner", "outer"]:  # Example modes
            self._region_mode = value
        else:
            raise ValueError("Invalid region mode. Choose from 'none', 'rectangular', or 'circular'.")

    # Getter for _comp_selection (read-only)
    @property
    def comp_selection(self):
        return self._comp_selection

    # Getter for _output_labels (read-only)
    @property
    def output_labels(self):
        return self._output_labels


    def mix_and_display(self, selector_region, min_height, min_width, images, weights):
        """Mix images and display the result in real-time, with progress updates."""
        try:
            mixed_image = self.__mix_images(selector_region, min_height, min_width, images, weights)
            self.__display_mixed_image(mixed_image)
        except Exception as e:
            print(f"Error during real-time mixing: {e}")

    def __mix_images(self, selector_region,min_height,min_width,images,weights):
        """Mix images using their Fourier Transform components and weights."""
        if min_width is None or min_height is None:
            print("Error: Images are not preprocessed for consistent dimensions.")
            return np.zeros((100, 100), dtype=np.uint8)  # Placeholder blank image

        # Initialize combined FT arrays for real and imaginary parts
        combined_ft_real = np.zeros((min_height, min_width), dtype=np.float64)
        combined_ft_imag = np.zeros((min_height, min_width), dtype=np.float64)
        combined_ft_magnitude = np.zeros((min_height, min_width), dtype=np.float64)
        combined_ft_phase = np.zeros((min_height, min_width), dtype=np.float64)
        real_mag = np.zeros((min_height, min_width), dtype=np.float64)
        imag_mag = np.zeros((min_height, min_width), dtype=np.float64)
        magnitude= np.zeros((min_height, min_width), dtype=np.float64)


        for i in range(4):
            if images[i] is None or weights[i] == 0.0:
                continue  # Skip if no image is loaded or weight is zero
            weight = weights[i]
            # Get the Fourier Transform of the image
            ft_image = np.fft.fft2(images[i])
            ft_image_shifted = np.fft.fftshift(ft_image)  # Shift for visualization/mixing

            # Apply user-selected region mask if enabled
            ft_image_shifted = self.__apply_region_mask(ft_image_shifted,selector_region)

            # Extract the selected FT component
            selected_component = self.comp_selection[i].currentText()
            if selected_component == "FT Magnitude":
                real_part = np.real(ft_image_shifted) * weight
                imag_part = np.imag(ft_image_shifted) * weight
                magnitude = np.sqrt(real_part ** 2 + imag_part ** 2)
                phase = np.zeros_like(magnitude)
                real = np.zeros_like(magnitude)  # Reconstruct real part
                imag = np.zeros_like(magnitude)  # Reconstruct imaginary part
                real_mag +=real_part *0.1
                imag_mag +=imag_part
            elif selected_component == "FT Phase":
                real_part = np.real(ft_image_shifted) * weight
                imag_part = np.imag(ft_image_shifted)
                phase = np.arctan2(imag_part, real_part)  # Use np.arctan2 for array input
                magnitude = np.ones_like(phase)
                real = np.zeros_like(phase)  # Reconstruct real part
                imag = np.zeros_like(phase)  # Reconstruct imaginary part
                real_mag += real_part
                imag_mag += imag_part
            elif selected_component == "FT Real":
                real = np.real(ft_image_shifted)
                imag = np.zeros_like(real)  # Set imaginary part to 0
                phase = np.zeros_like(real)
                magnitude = np.zeros_like(real)
            elif selected_component == "FT Imaginary":
                imag = np.imag(ft_image_shifted)
                real = np.zeros_like(imag)  # Set real part to 0
                phase = np.zeros_like(imag)
                magnitude = np.zeros_like(imag)
            else:
                print(f"Unknown component: {selected_component}")
                continue

            # Apply weight to the FT components
            combined_ft_real += weight * real
            combined_ft_imag += weight * imag
            combined_ft_magnitude += magnitude
            combined_ft_phase += phase


        # Combine real and imaginary parts into a complex FT
        combined_ft_1 = combined_ft_real + 1j * combined_ft_imag
        combined_ft_2 = combined_ft_magnitude * np.exp(1j * combined_ft_phase)
        combined_ft = combined_ft_1 + combined_ft_2
        if np.all(combined_ft_1 ==0 ) and np.all(np.imag(combined_ft_2) ==0):
            combined_ft=self.__display_magnitude(real_mag,imag_mag)
        elif np.all(combined_ft_1 ==0 ) and np.all( combined_ft_magnitude <= 4):
            combined_ft=self.__display_magnitude(real_mag,imag_mag)
        # Apply inverse FFT to reconstruct the output image

        combined_ft_shifted = np.fft.ifftshift(combined_ft)  # Undo the shift
        mixed_image = np.fft.ifft2(combined_ft_shifted)  # Inverse FFT
        mixed_image = np.abs(mixed_image)  # Take magnitude for the output

        # Normalize and return the mixed image
        mixed_image = cv2.normalize(mixed_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return mixed_image

    def __display_mixed_image(self, mixed_image):
        """Display the mixed image in the output labels."""

        qt_image = self.convert.convert_cv_to_qt(mixed_image)
        if qt_image is not None:
            pixmap = QPixmap.fromImage(qt_image)
            if self.ui.outputSelectioncomboBox.currentText() == "output_1":

                self.output_labels[0].setPixmap(pixmap.scaled(self.output_labels[0].size(), Qt.KeepAspectRatio))
            else:

                self.output_labels[1].setPixmap(pixmap.scaled(self.output_labels[1].size(), Qt.KeepAspectRatio))



    def __apply_region_mask(self, ft_data, selector_region):
        """
        Apply a mask to the FT data based on the selected region and mode (inner/outer).
        """
        height, width = ft_data.shape
        mask = np.zeros_like(ft_data, dtype=np.uint8)

        # Region dimensions
        x, y, w, h = selector_region
        x = max(0, min(x, width - w))
        y = max(0, min(y, height - h))

        # Create the mask
        if self.region_mode == "inner":
            mask[y:y + h, x:x + w] = 1  # Inner region is 1, rest is 0
        elif self.region_mode == "outer":
            mask[:, :] = 1  # Entire mask is 1
            mask[y:y + h, x:x + w] = 0  # Inner region is set to 0
        elif self.region_mode == "none":
            mask[:, :] = 1  # No masking applied, entire image is used

        # Apply the mask to the FT data
        masked_ft = ft_data * mask
        return masked_ft

    def update_region_mode(self,selector_region,min_height,min_width,images,weights):
        """Update the region mode based on the selected radio button."""
        if self.ui.inner_region.isChecked():
            self.region_mode = "inner"
        elif self.ui.outer_region.isChecked():
            self.region_mode = "outer"
        elif self.ui.none_region.isChecked():  # New condition for None
            self.region_mode = "none"  # Set region mode to None
        else:
            self.region_mode = None  # No region selected

        print(f"Region mode updated to: {self.region_mode}")
        # Start mixing in a separate thread


    def __display_magnitude(self,real,imag):
        print("hello")
        magnitude=np.sqrt(real ** 2+imag ** 2)
        phase = np.atan(real,imag)
        return magnitude * np.exp(1j * phase)