import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from Images import ImageHandler
from FFT import FFTHandler
import cv2  # OpenCV for image processing
from PyQt5.QtCore import Qt
from Design import Ui_MainWindow
from PyQt5.QtWidgets import QFileDialog
from ImagesMixing import ImagesMixing
from Threading import WorkerThread ,WorkerSignals

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()  # Initialize the user interface
        self.ui.setupUi(self)  # Set up the UI

        # Initialize handlers
        self.image_handler = ImageHandler(self.ui)
        self.image_mixing= ImagesMixing(self.ui)
        self.fft_handler = FFTHandler(self.image_handler,self.ui,self.image_mixing)
        self.worker_signals = WorkerSignals()
        self.worker_thread = WorkerThread(5, self.worker_signals, self)

        self.active_image_index = None  # Track the active image index

        self.images = [None] * 4
        self.image_labels = [
            self.ui.input_image_1,
            self.ui.input_image_2,
            self.ui.input_image_3,
            self.ui.input_image_4
        ]
        self.FT_image_labels = [
            self.ui.FT_components_1,
            self.ui.FT_components_2,
            self.ui.FT_components_3,
            self.ui.FT_components_4
        ]
        self.comp_selection = [
            self.ui.comp_selection_1,
            self.ui.comp_selection_2,
            self.ui.comp_selection_3,
            self.ui.comp_selection_4
        ]
        self.reset_buttons = [
            self.ui.reset_button_1,
            self.ui.reset_button_2,
            self.ui.reset_button_3,
            self.ui.reset_button_4
        ]
        self.weight_sliders = [
            self.ui.horizontalSlider_1,
            self.ui.horizontalSlider_2,
            self.ui.horizontalSlider_3,
            self.ui.horizontalSlider_4
        ]

        self.ui.none_region.setChecked(True)  # Default to Magnitude Phase
        self.ui.none_region.clicked.connect(lambda :self.fft_handler.reset(self))
        self.ui.inner_region.clicked.connect(lambda :self.fft_handler.reset(self))
        self.ui.outer_region.clicked.connect(lambda :self.fft_handler.reset(self))

        # Connect UI signals to handlers
        self.setup_ui_connections()

        self.ui.quit_button.clicked.connect(sys.exit)

    def setup_ui_connections(self):
        # Connect double-click events to load images
        for i in range(4):
            self.image_labels[i].mouseDoubleClickEvent = lambda event, idx=i: self.load_image(idx)

        for combo in self.comp_selection:
            combo.currentIndexChanged.connect(lambda:self.fft_handler.update_display(self.images,self.image_handler.min_height,self.image_handler.min_width,self.weights))

        # Connect mouse events for brightness/contrast adjustment
        for i, label in enumerate(self.image_labels):
            label.setMouseTracking(True)
            label.mousePressEvent = lambda event, idx=i: self.mouse_press_event(event, idx)
            label.mouseMoveEvent = lambda event, idx=i: self.mouse_move_event(event, idx)

        # Connect reset buttons to reset method
        for idx, button in enumerate(self.reset_buttons):
            button.clicked.connect(lambda checked, index=idx: self.reset_brightness_contrast(index))

        self.ui.outputSelectioncomboBox.addItems(["output_1", "output_2"])
        self.ui.outputSelectioncomboBox.setCurrentText("output_1")

        # Initialize weights for mixing
        self.weights = [0.0] * 4  # Default weights for each image



        self.ui.horizontalSlider_1.sliderReleased.connect(lambda : self.update_weight(self.ui.horizontalSlider_1.value(), 0))
        self.ui.horizontalSlider_2.sliderReleased.connect(lambda : self.update_weight(self.ui.horizontalSlider_2.value(), 1))
        self.ui.horizontalSlider_3.sliderReleased.connect(lambda : self.update_weight( self.ui.horizontalSlider_3.value(),2))
        self.ui.horizontalSlider_4.sliderReleased.connect(lambda : self.update_weight(self.ui.horizontalSlider_4.value(),3))


        # Connect the region selection slider to update selectors
        # Assuming update_selectors takes parameters
        self.ui.regionSelectionSlider.sliderReleased.connect(lambda : self.fft_handler.update_selectors(self.ui.regionSelectionSlider.value(),self.image_handler.min_height,self.image_handler.min_width,self.images,self.weights,self))
        self.ui.regionSelectionSlider.setRange(0, 380)  # Minimum: 50, Maximum: 400
        # Connect the group to your handler
        self.ui.region_group.buttonToggled.connect(lambda : self.image_mixing.update_region_mode(self.fft_handler.selector_region,self.image_handler.min_height,self.image_handler.min_width,self.images,self.weights ))


        # Connect buttons
        # self.ui.start_mix_button.clicked.connect(self.start_ifft)
        #self.ui.cancel_button.clicked.connect(self.ifft.cancel_ifft)

        # Connect the group to your handler
        self.ui.ft_component_group.buttonToggled.connect(self.on_ft_component_toggled)

    def load_image(self, index):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                                   "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)", options=options)
        if file_name:
            try:
                # Load and convert to grayscale
                image = cv2.imread(file_name)
                if image is not None:
                    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    self.images[index] = gray_image
                    self.image_handler.display_images(self.images)
                    self.fft_handler.FT_images[index] = None
                    self.fft_handler.update_display(self.images,self.image_handler.min_height,self.image_handler.min_width,self.weights)
                    self.reset_brightness_contrast(index)
                    self.ui.none_region.setChecked(True)
                    self.ui.magnitude_phase.setChecked(True)  # Default to Magnitude Phase
                    self.ui.real_imaginary.setChecked(False)  # Ensure the other is deselected
                    if self.ui.real_imaginary.isChecked():
                        self.ui.magnitude_phase.setChecked(False)  # Default to Magnitude Phase
                        self.ui.real_imaginary.setChecked(True)

                else:
                    print("Error: Could not read the image.")
            except Exception as e:
                print(f"An error occurred: {e}")

    def update_weight(self,value, index):
        """Update the weight for the specified image index and mix in real-time."""
        self.weights[index] =value / 100.0  # Normalize weight to [0, 1]
        self.start_thread()
    def on_ft_component_toggled(self, button, checked):
        if checked:
            component_type = "Magnitude Phase" if button == self.ui.magnitude_phase else "Real Imaginary"
            print(f"{component_type} radio button is selected.")
            self.on_radio_toggled(checked, component_type)

    def on_radio_toggled(self, checked, component_type):
        if checked:  # Radio button is selected
            print(f"{component_type} radio button is selected")

            # Map component_type to the corresponding FT components
            component_map = {
                "Magnitude Phase": ["FT Magnitude", "FT Phase"],
                "Real Imaginary": ["FT Real", "FT Imaginary"]
            }

            components = component_map.get(component_type, [])

            # Clear current items in combo boxes before adding new ones
            for combo in self.comp_selection:
                combo.clear()  # Clear the current items

            # Populate combo boxes with the relevant components
            for combo in self.comp_selection:
                combo.addItems(components)
        else:  # Radio button is deselected
            print(f"{component_type} radio button is deselected")

            # Map component_type to the corresponding FT components
            component_map = {
                "Magnitude Phase": ["FT Magnitude", "FT Phase"],
                "Real Imaginary": ["FT Real", "FT Imaginary"]
            }

            components = component_map.get(component_type, [])

            # Find the indexes of the components to remove
            index_list = [0, 0]
            for index in range(1, 5):
                if self.comp_selection[0].itemText(index) == components[0]:
                    index_list[0] = index
                elif self.comp_selection[0].itemText(index) == components[1]:
                    index_list[1] = index

            # Remove the corresponding components from the combo boxes
            for combo in self.comp_selection:
                if index_list[1] != 0:
                    combo.removeItem(index_list[1])
                if index_list[0] != 0:
                    combo.removeItem(index_list[0])

    def mouse_press_event(self, event, index):
        self.active_image_index = index
        self.last_mouse_y = event.y()
        self.last_mouse_x = event.x()

    def mouse_move_event(self, event, index):
        if self.active_image_index == index and event.buttons() == Qt.LeftButton:
            dy = event.y() - self.last_mouse_y
            dx = event.x() - self.last_mouse_x

            # Adjust brightness and contrast based on mouse movement
            self.image_handler.brightness[index] += dy  # Increase brightness when moving up, decrease when moving down
            self.image_handler.contrast[index] += dx * 0.01  # Increase contrast when moving right, decrease when moving left

            self.image_handler.display_images(self.images)  # Update the display
            self.last_mouse_y = event.y()
            self.last_mouse_x = event.x()

    def reset_brightness_contrast(self, index):
        """Reset brightness and contrast for the specified image index."""
        self.image_handler.brightness[index] = 0
        self.image_handler.contrast[index] = 1.0
        self.image_handler.display_images(self.images)  # Update the display for the specific image

    def start_thread(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.cancel()

        self.worker_signals.canceled.clear()
        self.worker_thread = WorkerThread(5, self.worker_signals, self)
        self.worker_thread.start()

    def collect_chunks(self):
        for ind in range(4):
            if self.images[ind] is not None:
                self.image_mixing.chunks[str(ind)] = self.fft_handler.FT_images[ind]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
