from itertools import count
from operator import truediv

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QMessageBox, QVBoxLayout,
    QLineEdit, QLabel, QComboBox, QPushButton, QGridLayout, QMenu
)
from PyQt6 import uic
from database import (
    get_tables, add_table, delete_table, update_table_status,
    get_all_dishes, add_dish, update_dish, delete_dish,db_connection,get_user_role
)
import datetime


class TableSelectionWindow(QMainWindow):
    # 餐桌选着的主页面
    update_signal = pyqtSignal()  # 用于触发界面的刷新，pyqtSignal()是pyqt实现信号和槽机制，用于触发。定义了一个信号

    def __init__(self, username):
        super().__init__()
        uic.loadUi("ui/order_table.ui", self)  # 加载UI文件

        self.username = username  # 将open_main_window中传递进来的用户名接受并保存
        self.user_role = self.get_user_role()  # 获取用户角色
        #print(f"用户角色: {self.user_role}")
        self.init_ui()  # 初始化ui界面
        self.update_signal.connect(self.load_tables)  # 绑定信号到餐桌到加载
        self.setup_shortcuts()  # 设置快捷键
        self.setup_timer()  # 启动时间更新定时器

        # 默认进入全屏模式
        self.enter_fullscreen()



    def init_ui(self):
        # 初始化用户名和时间显示
        self.findChild(QLabel, "label_username").setText(f"用户：{self.username}")
        self.time_label = self.findChild(QLabel, "label_time")

        # 查找并绑定按钮事件
        self.add_table_btn = self.findChild(QPushButton, "add_table_btn")
        self.del_table_btn = self.findChild(QPushButton, "del_table_btn")
        self.fullscreen_btn = self.findChild(QPushButton, "fullscreen_btn")
        self.dish_manage_btn = self.findChild(QPushButton, "dish_manage_btn")
        self.history_orders_btn = self.findChild(QPushButton, "history_orders_btn")

        # 根据用户角色显示或隐藏特定按钮
        if self.user_role == True:  # 管理员角色
            self.add_table_btn.show()
            self.del_table_btn.show()
            self.dish_manage_btn.show()
            self.history_orders_btn.show()
        else:  # 普通用户角色
            self.add_table_btn.hide()
            self.del_table_btn.hide()
            self.dish_manage_btn.hide()
            self.history_orders_btn.show()

        # 绑定按钮点击事件
        self.add_table_btn.clicked.connect(self.show_add_dialog)
        self.del_table_btn.clicked.connect(self.show_del_dialog)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.history_orders_btn.clicked.connect(self.show_history_orders)



        # 初始化菜品管理下拉菜单
        self.setup_dish_manage_menu()

        # 首次加载餐桌数据
        self.load_tables()

#获取用户角色
    def get_user_role(self):

        return get_user_role(self.username)

#显示历史订单
    def show_history_orders(self):
        try:
            from history_orders import HistoryOrdersWindow
            self.history_window = HistoryOrdersWindow(self.username)
            self.history_window.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示历史订单时发生错误: {str(e)}")

    def setup_dish_manage_menu(self):
        # 创建菜品下拉菜单
        self.dish_menu = QMenu()
        # 添加菜单项
        action_add = QAction("添加菜品", self)
        action_edit = QAction("修改菜品", self)
        action_delete = QAction("删除菜品", self)
        # 绑定对应的函数动作
        action_add.triggered.connect(self.show_add_dish_dialog)
        action_edit.triggered.connect(self.show_edit_dish_dialog)
        action_delete.triggered.connect(self.show_delete_dish_dialog)
        # 将动作添加到菜单
        self.dish_menu.addAction(action_add)
        self.dish_menu.addAction(action_edit)
        self.dish_menu.addAction(action_delete)
        # 绑定按钮点击事件显示菜单 mapToGlobal和rect().bottomLeft()的作用是获取按钮左下角的位置
        # ，确保菜单从按钮的左下角弹出。

        #绑定按钮点击事件
        self.dish_manage_btn.clicked.connect(
            #定义一个匿名函数，用于延迟执行菜单显示操作。
            #直接调用 self.dish_menu.exec() 会导致菜单立即显示，而使用 lambda 可以在按钮点击时才执行。
            lambda: self.dish_menu.exec(
                self.dish_manage_btn.mapToGlobal(
                    #获取按钮左下角的坐标点（相对于按钮自身）
                    self.dish_manage_btn.rect().bottomLeft()
                )
            )
        )

    #创建一个快捷键ESC用于全屏
    def setup_shortcuts(self):
        self.exit_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.exit_shortcut.activated.connect(self.exit_fullscreen)
    #定时器 用于显示当前的事件，定时一秒刷新
    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)


    #获取当前的事件
    def update_time(self):
        #获取当前时间
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #将标签控件 self.time_label 的文本设置为 f"时间：{current_datetime}"
        self.time_label.setText(f"时间：{current_datetime}")

    #从数据库中加载餐桌信息并生成按钮
    def load_tables(self):
        # 查找gridLayout布局并清理旧的按键
        grid_layout = self.findChild(QGridLayout, "gridLayout")
        #清理掉旧的按键，grid_layout.count() 获取布局中的控件数量。
        while grid_layout.count():
            #移除索引为 0 的控件，每次循环后布局中的第一个控件都会被移除
            item = grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                #安排控件在事件循环中删除，确保界面刷新时旧按钮被清理掉。
                widget.deleteLater()
        #获取餐桌的数据
        tables = get_tables()
        # 生成按钮同时更新界面
        row, col = 0, 0
        #遍历餐桌信息
        for table in tables:
            #创建按钮并设置属性
                # 创建一个按钮，显示餐桌名称和状态的文本。
                # 设置按钮的固定大小为 120 像素宽、80 像素高。
                # 根据餐桌的状态设置按钮的样式（如背景颜色）。
            btn = QPushButton(f"餐桌 {table['name']}\n({self.get_status_text(table['status'])})")
            btn.setFixedSize(120, 80)
            btn.setStyleSheet(self.get_status_style(table['status']))
            #将按钮的点击事件连接到 open_table 方法，用于打开对应的餐桌详情界面。
            btn.clicked.connect(lambda _, t=table: self.open_table(t))
            #将按键添加到网格布局当中
            #同时最多3个每行，还多的往下创建下一行
            grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

    #获取餐桌的状态。其他状态还没想好是啥
    def get_status_text(self, status):
        return {0: "空闲", 1: "使用中", 2: "未结账"}.get(status, "未知状态")
    #状态的样式
    def get_status_style(self, status):
        return {
            0: "background-color: #90EE90;",  # 空闲-绿色
            1: "background-color: #FFB6C1;",  # 使用中-粉色
            2: "background-color: #FFD700;"  # 未结账-黄色
        }.get(status, "background-color: white;")

    #打开餐桌
    def open_table(self, table):
        #尝试打开点餐窗口
        try:
            #从order_dishes模块中导入OrderDishesWindow类（点餐界面的窗口）
            from order_dishes import OrderDishesWindow
            #创建一个点餐界面的实例同时传入餐桌号和用户名
            self.order_window = OrderDishesWindow(table["name"], self.username)
            self.order_window.show()
            self.close()
        #异常处理
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开点菜界面失败: {str(e)}")

    #添加餐桌对话框
    def show_add_dialog(self):
        #创建一个实例指定为添加“add”
        #self参数表示当前窗口作为对话框的父窗口。
        dialog = TableDialog("add", self)
        #执行对话框
        #调用exec()方法显示对话框，并进入事件循环等待用户操作。
        #如果用户点击了对话框中的确认按钮（如“确定”或“添加”），exec()方法返回QDialog.DialogCode.Accepted。
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_signal.emit()

    # 删除餐桌对话框
    def show_del_dialog(self):
        #解释同上
        dialog = TableDialog("del", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_signal.emit()

    #检查当前窗口是否处于全屏模式。
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()
    #退出全面
    def enter_fullscreen(self):
        self.showFullScreen()
        self.fullscreen_btn.setText("退出全屏")
    #进入全屏
    def exit_fullscreen(self):
        self.showNormal()
        self.fullscreen_btn.setText("进入全屏")


    #添加菜品
    def show_add_dish_dialog(self):
        # 创建对话框
        dialog = DishDialog(mode="add", parent=self)
        ##执行对话框
        # 显示对话框等待用户操作如果用户点击确认则返回值为QDialog.DialogCode.Accepted
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "成功", "菜品添加成功！")
            self.update_signal.emit()
    #修改菜品
    def show_edit_dish_dialog(self):
        # 创建一个用于修改现有菜品的对话框。
        dialog = DishDialog(mode="edit", parent=self)
        #执行对话框：dialog.exec() 显示对话框并等待用户操作。如果用户点击确认按钮，返回值为 QDialog.DialogCode.Accepted。
        if dialog.exec() == QDialog.DialogCode.Accepted:
            #显示一个消息框，提示用户菜品修改成功。
            QMessageBox.information(self, "成功", "菜品修改成功！")
            # 发出信号，通知界面刷新菜品列表
            self.update_signal.emit()
    #删除菜品
    def show_delete_dish_dialog(self):
        #基本都同上
        dialog = DishDialog(mode="delete", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "成功", "菜品删除成功！")
            self.update_signal.emit()

#添加或删除餐桌的对话框
class TableDialog(QDialog):
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode#添加模式为add or del mode从show_add_dialog方式中调入
        self.setWindowTitle("添加餐桌" if mode == "add" else "删除餐桌")
        layout = QVBoxLayout()# 创建一个垂直布局

        #模式判断是添加还是删除
        if mode == "add":
            self.name_input = QLineEdit()
            layout.addWidget(QLabel("餐桌名称："))
            layout.addWidget(self.name_input)
        else:
            self.tables_combo = QComboBox()
            tables = get_tables()
            for table in tables:
                self.tables_combo.addItem(table["name"])
            layout.addWidget(QLabel("选择要删除的餐桌："))
            layout.addWidget(self.tables_combo)
        #确认按钮
        btn_confirm = QPushButton("确认")
        btn_confirm.clicked.connect(self.confirm_action)
        layout.addWidget(btn_confirm)
        self.setLayout(layout)

    #添加和删除选项
    def confirm_action(self):
        if self.mode == "add":
            name = self.name_input.text().strip() #获取到新建的餐桌名称
            if not name:#如果为空则
                QMessageBox.warning(self, "错误", "请输入餐桌名称")
                return
            if add_table(name): ## 调用 add_table 函数添加餐桌
                QMessageBox.information(self, "成功", "餐桌添加成功！")
                self.accept() # 关闭对话框并返回接受状态
            else:
                QMessageBox.warning(self, "错误", "餐桌名称已存在")
        else: #如果为删除
            table_name = self.tables_combo.currentText()#获取到被删除的餐桌名称
            if delete_table(table_name): ## 调用 delete_table 函数删除餐桌
                QMessageBox.information(self, "成功", "餐桌删除成功！")#显示成功消息框
                self.accept()# 关闭对话框并返回接受状
            else:
                QMessageBox.warning(self, "错误", "删除失败")

#管理菜品的添加、修改和删除操作
class DishDialog(QDialog):
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode#菜品模式
        self.setWindowTitle("添加菜品" if mode == "add" else "修改菜品" if mode == "edit" else "删除菜品")
        self.setup_ui()

    #根据模式初始化界面
    def setup_ui(self):
        from database import get_all_dishes
        layout = QVBoxLayout()

        if self.mode in ["add", "edit"]:
            #公共的输入字段
            self.name_input = QLineEdit()
            self.price_input = QLineEdit()
            self.category_combo = QComboBox()
            self.category_combo.addItems(["冷菜", "热菜", "酒水", "其他"])
            #添加控件
            layout.addWidget(QLabel("菜品名称："))
            layout.addWidget(self.name_input)
            layout.addWidget(QLabel("价格："))
            layout.addWidget(self.price_input)
            layout.addWidget(QLabel("分类："))
            layout.addWidget(self.category_combo)

            if self.mode == "edit":
                # 如果是修改则需要选择对应的菜品
                self.dish_combo = QComboBox()
                dishes = get_all_dishes()
                for dish in dishes:
                    self.dish_combo.addItem(dish["name"], dish["id"])
                layout.addWidget(QLabel("选择菜品："))
                layout.addWidget(self.dish_combo)

        elif self.mode == "delete":
            # 删除模式下。显示菜品列表
            self.dish_combo = QComboBox()
            dishes = get_all_dishes()
            for dish in dishes:
                self.dish_combo.addItem(dish["name"], dish["id"])
            layout.addWidget(QLabel("选择要删除的菜品："))
            layout.addWidget(self.dish_combo)

        # 确认按钮
        btn_confirm = QPushButton("确认")
        btn_confirm.clicked.connect(self.confirm_action)
        layout.addWidget(btn_confirm)
        self.setLayout(layout)

    #执行菜品管理操作
    def confirm_action(self):
        from database import add_dish, update_dish, delete_dish
        try:
            if self.mode == "add":
                # 添加菜品
                name = self.name_input.text().strip()
                price = float(self.price_input.text())
                category = self.category_combo.currentText()
                if add_dish(name, price, category):
                    self.accept()
                else:
                    QMessageBox.warning(self, "错误", "菜品名称已存在！")

            elif self.mode == "edit":
                ## 修改菜品
                dish_id = self.dish_combo.currentData()
                new_name = self.name_input.text().strip()
                new_price = float(self.price_input.text())
                new_category = self.category_combo.currentText()
                if update_dish(dish_id, new_name, new_price, new_category):
                    self.accept()
                else:
                    QMessageBox.warning(self, "错误", "修改失败！")
            ## 删除菜品
            elif self.mode == "delete":
                dish_id = self.dish_combo.currentData()
                if delete_dish(dish_id):
                    self.accept()
                else:
                    QMessageBox.warning(self, "错误", "删除失败！")

        except ValueError:
            QMessageBox.critical(self, "错误", "价格必须为数字！")

