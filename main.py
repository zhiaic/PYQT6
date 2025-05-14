import sys
from PyQt6.QtWidgets import QApplication
from login_register import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置全局样式
    # app.setStyleSheet("""
    #     QMainWindow { background: #f0f4f7; }
    #     QPushButton {
    #         min-width: 100px;
    #         padding: 8px;
    #         border-radius: 4px;
    #     }
    # """)


    #创建并显示登录窗口，并显示
    login_window = LoginWindow()
    login_window.show()
    #进入事件循环（app.exec()）
    sys.exit(app.exec())