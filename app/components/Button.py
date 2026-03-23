from PySide6.QtWidgets import QPushButton

class Button:
    def __init__(self, text: str):
        self.text = text

    def default_button(self) -> QPushButton:
        btn = QPushButton(self.text)
        btn.setMinimumHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #6A1B9A;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #4A148C;
            }
        """)
        return btn