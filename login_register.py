from PyQt6.QtWidgets import QMainWindow, QLineEdit, QPushButton, QMessageBox, QDialog
from PyQt6 import uic

import traceback
from database import login_user, register_user # 导入database.py中的函数login_user, register_user登陆和注册
from order_tables import TableSelectionWindow  # 导入新的餐桌选择窗口类
from datetime import datetime



class LoginWindow(QMainWindow):
    #用户登录主窗口，负责处理登录验证和注册功能跳转
    def __init__(self):
        super().__init__()
        # 加载登录界面UI文件
        uic.loadUi("ui/login.ui", self)

        # 控件获取
        self.txt_username = self.findChild(QLineEdit, "username_edit") #账号输入框
        self.txt_password = self.findChild(QLineEdit, "password_edit")#密码输入框
        self.btn_login = self.findChild(QPushButton, "login_btn")#登陆按钮
        self.btn_register = self.findChild(QPushButton, "btn_register")#注册按钮

        # 事件绑定
        self.btn_login.clicked.connect(self.login) #连接登陆按键的事件
        self.btn_register.clicked.connect(self.show_register)#注册按钮点击事件

    def login(self):
        """用于处理用户登陆的逻辑"""
        username = self.txt_username.text().strip() #用于获取登陆注册的文本 strip()是用来去除首尾的空白字符
        password = self.txt_password.text().strip()

        #调用数据库中的登陆验证函数，判断验证账号密码是否正确
        if login_user(username, password):
            QMessageBox.information(self, "成功", "登录成功！")
            self.open_main_window(username)  # 打开餐桌选择窗口并传递用户名
        else:
            QMessageBox.warning(self, "错误", "账号或密码错误")
            self.txt_password.clear()

    #显示注册框
    def show_register(self):
        try:
            register_dialog = self.RegisterDialog() ## 创建注册对话框实例
            register_dialog.exec()  # 调用个exec执行register_dialog对话实例
        except Exception as e:
            # 捕获并显示异常详细信息
            QMessageBox.critical(self, "错误", f"发生错误: {str(e)}") # 显示错误信息
            traceback.print_exc()  # # 打印完整错误堆栈（调试用）
    #打开餐桌选着窗口
    def open_main_window(self, username):
        # 创建餐桌选择窗口实例并传递用户名
        self.table_window = TableSelectionWindow(username)  # 创建餐桌选择窗口实例
        self.table_window.show() #显示餐桌选择窗口
        self.close() ## 关闭登录窗口 到此跳转到了餐桌选择的实例

## 注册对话框类

    #注册对话框，处理注册的逻辑
    class RegisterDialog(QDialog):
        def __init__(self):
            super().__init__()
            try:
                #加载ui
                uic.loadUi("ui/register.ui", self)

                self.txt_username = self.findChild(QLineEdit, "txt_username") ## 用户名输入框
                self.txt_password = self.findChild(QLineEdit, "txt_password") #密码输入框
                self.txt_confirm = self.findChild(QLineEdit, "txt_confirm")  # 确认密码输入框
                self.btn_register = self.findChild(QPushButton, "btn_register") # 注册按钮

                #绑定注册按钮点击事件
                self.btn_register.clicked.connect(self.register)
            except Exception as e:
                #初始化失败处理
                QMessageBox.critical(self, "错误", f"初始化错误: {str(e)}")
                traceback.print_exc()

            #注册逻辑
        def register(self):
            try:
                #获取并去除掉首末尾的除空格
                username = self.txt_username.text().strip()
                password = self.txt_password.text().strip()
                confirm = self.txt_confirm.text().strip()
                #输入校验
                if not all([username, password, confirm]):
                    QMessageBox.warning(self, "错误", "所有字段必须填写")
                    return

                if password != confirm:
                    QMessageBox.warning(self, "错误", "两次密码输入不一致")
                    return
                #调用数据库注册函数 进行一个注册 成功后关闭窗口
                if register_user(username, password):
                    QMessageBox.information(self, "成功", "注册成功！")
                    self.accept()#关闭对话框
                else:
                    QMessageBox.warning(self, "错误", "用户名已存在")
            except Exception as e:
                # 注册过程异常处理
                QMessageBox.critical(self, "错误", f"注册失败: {str(e)}")
                traceback.print_exc()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication([])
    window = LoginWindow()
    window.show()
    app.exec()