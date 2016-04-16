APPSTYLE = """
QMenuBar { background: #192532; color: #DDDDDD }
QMenuBar::item { background-color: #192532 }
QMenuBar::item:selected { background-color: #141C26 }
QMenuBar::item:pressed { background-color: #141C26 }
QTextEdit#text_out {
    background: #12171C;
    color: #DDDDDD;
    border: 2px solid #1C2E40;
    border-radius: 5px;
}
QLineEdit#text_in {
    background-color: #12171C;
    border: 2px solid #1C2E40;
    border-radius: 5px;
    color: #DDDDDD;
    padding: 3px 3px 3px 3px;
}
QFrame#main_frame { background-color: black }
QFrame#right_frame { background-color: black }
QLabel { color: #DDDDDD }
QLabel#stats { margin: 10px 0px 2px -5px; padding: 0 0 0 3px; text-align: left}
QMessageBox { background-color: black }
QProgressBar {
    background-color: black;
    text-align: left;
    border: 2px solid #1C2E40;
    border-radius: 5px;
    color: #DDDDDD;
}
QProgressBar::chunk { background-color: #1C2E40}
QProgressBar#bar_rt {
    border: 2px solid #280C0C;
}
QProgressBar#bar_rt::chunk {
    background-color: #280C0C;
}
QDialog {
    background-color: #192532;
}
QDialog QCheckBox {
    color: #DDDDDD;
}
QDialog QPushButton {
    padding: 5px;
    background-color: #455363;
    border: 2px solid #455363;
    border-radius: 5px;
    color: #DDDDDD;
}
QDialog QSpinBox, QDialog QDoubleSpinBox {
    background-color: black;
    border: 2px solid #455363;
    border-radius: 5px;
    color: #DDDDDD;
}
/*QDialog QComboBox {
    border: 2px solid #455363;
    border-radius: 5px;
}
QDialog QComboBox::drop-down {
    subcontrol-origin: border;
    subcontrol-position: top right;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    border-width: 1px;
    background-color: #455363;
    color: white;
}
QDialog QComboBox::item { color: black; }
QDialog QComboBox::drop-down:hover { background-color: red; }*/
QDialog QSpinBox::up-button, QDialog QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    border-top-right-radius: 5px;
    border-width: 1px;
    background-color: #455363;
}
QDialog QSpinBox::down-button, QDialog QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    border-bottom-right-radius: 5px;
    border-width: 1px;
    background-color: #28303A;
}
"""
MACSTYLE = """
QScrollBar:vertical { border: none; background: #1C2E40; color: #1C2E40; }
QScrollBar::handle:vertical {
    border: 2px solid #213548;
    background-color: #192837;
    margin: 15px 0px 15px 0px;
}
QScrollBar::sub-line:vertical {
    background-color: #192837;
    border-top-right-radius: 5px;
    border: 2px solid #213548
}
QScrollBar::add-line:vertical {
    background-color: #192837;
    border-bottom-right-radius: 5px;
    border: 2px solid #213548
}
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical{
    border: 4px solid #192837;
    background-color: #213548
}
"""
# Qt/PyQt 5.5.1 Windows bug? where QScrollBar::handle:vertical behaves badly
MSSTYLE1 = """
QScrollBar:vertical {
    background: #1C2E40;
}
QScrollBar::sub-line:vertical {
    border-top-right-radius: 5px;
    border: 3px solid #213548;
}
QScrollBar::add-line:vertical {
    border-bottom-right-radius: 5px;
    border: 3px solid #213548;
}
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical{
    border: 4px solid #192837;
    background-color: #213548
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: #1C2E40;
}
"""
MSSTYLE2 = """
QScrollBar:vertical {
    background: #1C2E40;
}
QScrollBar::handle:vertical {
    background: #192837;
}
"""