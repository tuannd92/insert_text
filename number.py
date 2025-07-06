import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QGridLayout,
    QSlider,
    QComboBox
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from PIL import Image, ImageDraw, ImageFont

class BettingSlipEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chèn số")
        self.setGeometry(100, 100, 1200, 800)

        self.image_path = None
        self.original_pixmap = None
        self.current_pixmap = None
        self.font_size = 90  

        self.target_region = {
            "x": 341,  
            "y": 302,  
            "width": 120,  
            "height": 25,  
        }

        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout chính
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Panel điều khiển bên trái
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)

        # Panel hiển thị ảnh bên phải
        image_panel = self.create_image_panel()
        main_layout.addWidget(image_panel, 2)

    def create_control_panel(self):
        """Tạo panel điều khiển"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Nhóm chọn dấu số
        sign_group = QGroupBox("Chọn Dấu Số")
        sign_layout = QGridLayout()

        sign_layout.addWidget(QLabel("Dấu số:"), 0, 0)
        self.sign_combo = QComboBox()
        self.sign_combo.addItems(["Dương (+)", "Âm (-)"])
        self.sign_combo.currentTextChanged.connect(self.update_sign)
        sign_layout.addWidget(self.sign_combo, 0, 1)

        sign_group.setLayout(sign_layout)
        layout.addWidget(sign_group)

        # Nhóm nhập số
        number_group = QGroupBox("Nhập Số Mới (0-99)")
        number_layout = QGridLayout()

        # SpinBox cho số từ 0-99
        number_layout.addWidget(QLabel("Số mới:"), 0, 0)
        self.number_spinbox = QSpinBox()
        self.number_spinbox.setRange(0, 99)
        self.number_spinbox.setValue(0)
        self.number_spinbox.setFont(QFont("Arial", 12))
        self.number_spinbox.valueChanged.connect(self.generate_decimal)
        number_layout.addWidget(self.number_spinbox, 0, 1)

        # Decimal label
        number_layout.addWidget(QLabel("Số thập phân:"), 1, 0)
        self.decimal_label = QLabel("0.00")
        self.decimal_label.setFont(QFont("Arial"))
        number_layout.addWidget(self.decimal_label, 1, 1)

        # Hiển thị kết quả cuối cùng
        number_layout.addWidget(QLabel("Kết quả:"), 2, 0)
        self.result_label = QLabel("0.00")
        self.result_label.setFont(QFont("Arial", 12))
        self.result_label.setStyleSheet(
            "color: green; background-color: #f9f9f9; padding: 5px;"
        )
        number_layout.addWidget(self.result_label, 2, 1)

        number_group.setLayout(number_layout)
        layout.addWidget(number_group)

        # Nhóm tùy chỉnh font
        font_group = QGroupBox("Tùy Chỉnh Kích Thước Chữ")
        font_layout = QGridLayout()

        font_layout.addWidget(QLabel("Kích thước:"), 0, 0)
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(10, 1000)
        self.font_slider.setValue(90)
        self.font_slider.valueChanged.connect(self.update_font_size)
        font_layout.addWidget(self.font_slider, 0, 1)

        self.font_size_label = QLabel("90px")
        font_layout.addWidget(self.font_size_label, 1, 1)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Nhóm tọa độ
        position_group = QGroupBox("Tùy Chỉnh Vị Trí")
        position_layout = QGridLayout()

        position_layout.addWidget(QLabel("Tọa độ X:"), 0, 0)
        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(0, 2000)
        self.x_spinbox.setValue(self.target_region["x"])
        position_layout.addWidget(self.x_spinbox, 0, 1)

        position_layout.addWidget(QLabel("Tọa độ Y:"), 1, 0)
        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(0, 2000)
        self.y_spinbox.setValue(self.target_region["y"])
        position_layout.addWidget(self.y_spinbox, 1, 1)

        position_group.setLayout(position_layout)
        layout.addWidget(position_group)

        # Nhóm thao tác
        action_group = QGroupBox("Thao Tác")
        action_layout = QVBoxLayout()

        self.preview_btn = QPushButton("Xem Trước")
        self.preview_btn.clicked.connect(self.preview_changes)
        self.preview_btn.setEnabled(False)
        action_layout.addWidget(self.preview_btn)

        self.apply_btn = QPushButton("Áp Dụng Thay Đổi")
        self.apply_btn.clicked.connect(self.apply_changes)
        self.apply_btn.setEnabled(False)
        action_layout.addWidget(self.apply_btn)

        self.reset_btn = QPushButton("Khôi Phục Gốc")
        self.reset_btn.clicked.connect(self.reset_image)
        self.reset_btn.setEnabled(False)
        action_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("Lưu Ảnh")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.save_btn)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        layout.addStretch()
        return panel

    def create_image_panel(self):
        """Tạo panel hiển thị ảnh"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Label hiển thị ảnh
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 2px dashed #ccc; background-color: #f9f9f9;"
        )
        self.image_label.setText("Chọn ảnh để hiển thị")
        self.image_label.setMinimumSize(700, 500)

        # Cho phép click vào ảnh để chọn tọa độ
        self.image_label.mousePressEvent = self.image_clicked

        layout.addWidget(self.image_label)

        # Nhóm chọn ảnh
        file_group = QGroupBox("Chọn Ảnh")
        file_layout = QVBoxLayout()

        self.select_btn = QPushButton("Chọn Ảnh")
        self.select_btn.clicked.connect(self.select_image)
        file_layout.addWidget(self.select_btn)

        self.image_path_label = QLabel("Chưa chọn ảnh")
        self.image_path_label.setWordWrap(True)
        file_layout.addWidget(self.image_path_label)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Thông tin ảnh
        self.info_label = QLabel("Thông tin ảnh sẽ hiển thị ở đây")
        layout.addWidget(self.info_label)

        return panel

    def update_font_size(self, value):
        """Cập nhật kích thước font"""
        self.font_size = value
        self.font_size_label.setText(f"{value}px")

    def generate_decimal(self, value):
        """Tự động tạo số thập phân từ số nguyên với dấu âm/dương"""
        decimal_value = value / 100.0

        # Kiểm tra dấu được chọn
        if self.sign_combo.currentText() == "Âm (-)":
            decimal_value = -decimal_value

        formatted_decimal = f"{decimal_value:.2f}"

        self.decimal_label.setText(formatted_decimal)
        result_text = f"{formatted_decimal}"
        self.result_label.setText(result_text)

        # Cập nhật màu text dựa trên dấu
        self.update_text_color()

    def update_sign(self):
        """Cập nhật khi thay đổi dấu"""
        self.generate_decimal(self.number_spinbox.value())

    def update_text_color(self):
        """Cập nhật màu text dựa trên dấu âm/dương"""
        if self.sign_combo.currentText() == "Âm (-)":
            # Màu đỏ tối cho số âm
            self.result_label.setStyleSheet(
                "color: rgb(99, 40, 40); background-color: #f9f9f9; padding: 5px;"
            )
        else:
            # Màu xanh cho số dương
            self.result_label.setStyleSheet(
                "color: green; background-color: #f9f9f9; padding: 5px;"
            )

    def select_image(self):
        """Chọn ảnh từ máy tính"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn Ảnh Phiếu Cược",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)",
        )

        if file_path:
            self.image_path = file_path
            self.load_image()
            self.image_path_label.setText(f"Đã chọn: {os.path.basename(file_path)}")

            # Kích hoạt các nút
            self.preview_btn.setEnabled(True)
            self.apply_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

    def load_image(self):
        """Tải và hiển thị ảnh"""
        if self.image_path:
            self.original_pixmap = QPixmap(self.image_path)
            self.current_pixmap = self.original_pixmap.copy()

            # Resize ảnh để vừa với label
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            self.image_label.setPixmap(scaled_pixmap)

            # Hiển thị thông tin ảnh
            self.info_label.setText(
                f"Kích thước: {self.original_pixmap.width()}x{self.original_pixmap.height()}px"
            )

    def image_clicked(self, event):
        """Xử lý khi click vào ảnh để chọn tọa độ"""
        if self.original_pixmap:
            # Tính toán tọa độ thực tế trên ảnh gốc
            label_size = self.image_label.size()
            pixmap_size = self.original_pixmap.size()

            # Tỷ lệ scale
            scale_x = pixmap_size.width() / label_size.width()
            scale_y = pixmap_size.height() / label_size.height()

            # Tọa độ click
            click_x = int(event.pos().x() * scale_x)
            click_y = int(event.pos().y() * scale_y)

            # Cập nhật spinbox
            self.x_spinbox.setValue(click_x)
            self.y_spinbox.setValue(click_y)

          
    def replace_my_section_only(self, image_path):
        pil_image = Image.open(image_path)
        draw = ImageDraw.Draw(pil_image)

        x = self.x_spinbox.value()
        y = self.y_spinbox.value()

        # Tạo text mới
        decimal_text = self.decimal_label.text()
        new_text = f"{decimal_text}"

        # Thiết lập font
        try:
            font = ImageFont.truetype("framd.ttf", self.font_size) #framd
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", self.font_size)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", self.font_size)
                except:
                    font = ImageFont.load_default()

        # Tính kích thước text
        bbox = draw.textbbox((0, 0), new_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Tính lại vị trí vẽ để text căn giữa vào (x, y)
        text_x = x - text_width // 2
        text_y = y - text_height // 2

        # Tạo background cũng căn giữa
        padding_x = 18   
        padding_y = 17
        bg_x1 = text_x - padding_x
        bg_y1 = text_y - padding_y
        bg_x2 = text_x + text_width + padding_x
        bg_y2 = text_y + text_height + padding_y

        background_color = (16, 22, 36)
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=background_color)

        # Màu text dựa trên dấu âm/dương
        if self.sign_combo.currentText() == "Âm (-)":
            text_color = (236,69,67,255)  # Màu đỏ tối cho số âm
        else:
            text_color = (224,223,228,255)  # Màu trắng cho số dương

        draw.text((text_x, text_y), new_text, font=font, fill=text_color)

        return pil_image

    def preview_changes(self):
        """Xem trước thay đổi"""
        if not self.image_path:
            return

        preview_image = self.replace_my_section_only(self.image_path)

        temp_path = "temp_preview.png"
        preview_image.save(temp_path)

        preview_pixmap = QPixmap(temp_path)
        scaled_pixmap = preview_pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

        os.remove(temp_path)


    def apply_changes(self):
        """Áp dụng thay đổi vào ảnh"""
        if not self.image_path:
            return

        modified_image = self.replace_my_section_only(self.image_path)

        temp_path = "temp_applied.png"
        modified_image.save(temp_path)

        self.current_pixmap = QPixmap(temp_path)
        scaled_pixmap = self.current_pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

        os.remove(temp_path)


    def reset_image(self):
        """Khôi phục ảnh gốc"""
        if self.original_pixmap:
            self.current_pixmap = self.original_pixmap.copy()
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def save_image(self):
        """Lưu ảnh đã chỉnh sửa"""
        if not self.current_pixmap:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu Ảnh",
            f"betting_slip_{self.decimal_label.text()}.png",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
        )

        if file_path:
            self.current_pixmap.save(file_path)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BettingSlipEditor()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
