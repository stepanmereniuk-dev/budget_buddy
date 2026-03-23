from PySide6.QtWidgets import QLineEdit

class Input:
    def __init__(self, placeholder: str):
        self.placeholder = placeholder

    def default_input(self) -> QLineEdit:

        widget = QLineEdit()
        widget.setPlaceholderText(self.placeholder)
        widget.setMinimumHeight(50)
        
        widget.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f9f9f9;
                color: #333333;                   
            }
            QLineEdit:focus {
                border: 2px solid #6A1B9A;
            }
            QLineEdit::placeholder {
                color: #888888;                   
            }
        """)
        return widget