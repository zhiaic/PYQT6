import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton, QGridLayout, QMessageBox
from PyQt6 import uic

from database import update_table_status, get_dishes_by_category, db_connection, get_tables, delete_order, get_orders_by_table  # 导入从数据库获取菜品的函数
from datetime import datetime
import sqlite3
import json

#点菜和订单管理主窗口，负责菜品选择、订单保存和结账功能
class OrderDishesWindow(QMainWindow):
    def __init__(self, table_name, username):
        super().__init__()
        self.table_name = table_name
        self.username = username  # 保存用户名
        uic.loadUi('ui/order_dishes.ui', self)  # 加载UI文件

        # 设置窗口为全屏模式
        self.showFullScreen()
        self.fullscreen_btn.setText("退出全屏")  # 更新按钮文本

        self.selected_dishes = []

        # 设置信号槽
        self.search_box.textChanged.connect(self.search_dishes) # 搜索框输入事件
        self.tabWidget.currentChanged.connect(self.load_dishes) ## 标签页切换事件
        self.checkout_btn.clicked.connect(self.checkout)## 结账按钮
        self.exit_btn.clicked.connect(self.go_back_to_table_selection)  # 绑定退出按钮事件
        self.save_btn.clicked.connect(self.save_order)## 保存订单按钮
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)# 全屏切换

        # 删除按键绑定
        self.delete_order_btn.clicked.connect(self.delete_order)## 删除订单按钮

        # 初始化界面
        self.init_ui()

        # 加载已保存的订单
        self.load_saved_order()

    def init_ui(self):
        # 设置当前餐桌信息
        self.label_current_table.setText(f"当前餐桌: {self.table_name}")

        # 加载菜品
        self.load_dishes()
    # 加载已保存订单
    def load_saved_order(self):
        #从数据库加载未结账的订单
        orders = get_orders_by_table(self.table_name)
        if orders:
            latest_order = orders[0] # 获取最新订单
            menu_info = latest_order.get("menu_info")
            if menu_info:
                try:
                    self.selected_dishes = json.loads(menu_info) # 解析JSON数据
                    self.update_selected_dishes_display()## 刷新显示已选菜品
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    self.selected_dishes = []

    # 刷新显示已选菜品
    def update_selected_dishes_display(self):

        #将左侧菜品选择菜单旧内容删除
        while self.selected_dishes_layout.count() > 0:#count()：获取当前布局中的子控件数量。如果大于0则继续执行
            item = self.selected_dishes_layout.takeAt(0)#takeAt(0)：从布局中逐个取出子组件（索引从0开始）
            widget = item.widget()
            if widget: #检查该项目是否确实是一个控件。
                widget.deleteLater()#如果存在控件就删除


        #遍历选中的菜品并创建显示项
        for dish in self.selected_dishes:
            dish_layout = QHBoxLayout()#为每个菜品创建一个新的水平布局。
            dish_layout.setContentsMargins(0, 0, 0, 0)
            dish_layout.setSpacing(5)

            dish_label = QLabel()#创建一个标签显示菜品的名称、数量和价格。
            dish_label.setText(f"{dish['name']} x{dish['quantity']} - ¥{dish['total_price']:.2f}")
            dish_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: Microsoft YaHei;
                    font-size: 14px;
                }
            """)
            dish_layout.addWidget(dish_label, 1)

            # 创建一个删除按钮。
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-size: 14px;
                    padding: 10px 20px;
                    border-radius: 5px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3e8e41;
                }
            """)
            # 将删除按钮的点击事件连接到 delete_dish 方法。
            delete_btn.clicked.connect(lambda checked, d=dish: self.delete_dish(d))

            #创建一个容器控件。
            container = QWidget()
            #将水平布局设置为容器控件的布局。
            container.setLayout(dish_layout)
            #将容器控件添加到垂直布局中，以显示菜品信息。
            self.selected_dishes_layout.addWidget(container)

        #计算并更新金额显示
        #没有写优化的逻辑
        subtotal = sum(dish["price"] * dish["quantity"] for dish in self.selected_dishes)#
        discount = 0.0#设置折扣金额为 0。
        total = subtotal - discount#计算最终结账金额。
        #显示
        self.label_subtotal.setText(f"标价金额: ¥{subtotal:.2f}")
        self.label_discount.setText(f"折扣金额: ¥{discount:.2f}")
        self.label_total.setText(f"最后结账金额: ¥{total:.2f}")

    #用于菜品搜索功能
        #获取搜索文本：
    def search_dishes(self):
        #从搜索框中获取用户输入的文本，并去除首尾空格。
        search_text = self.search_box.text().strip()
        #如果搜索文本为空，直接返回，不执行后续操作。
        if not search_text:
            return

        #清除现有的菜品显示：
        while self.tab_all_dishes.layout().count() > 0:#检查当前标签页的布局中是否还有控件。
            item = self.tab_all_dishes.layout().takeAt(0)#逐一删除布局的控件，直到没有
            widget = item.widget()#获取该项目对应的控件。
            if widget:#是否是一个控件。
                widget.deleteLater()#在事件循环中删除

    #搜索菜品
        #初始化一个空列表，用于存储匹配的菜品
        matched_dishes = []
        #遍历所有菜品分类。
        for category in ["全部", "冷菜", "热菜", "酒水", "其他"]:
            #遍历当前分类下的每个菜品
            dishes = get_dishes_by_category(category)
            #遍历当前分类下的每个菜品
            for dish in dishes:
                #检索文本
                if search_text.lower() in dish["name"].lower():
                    #如果匹配，将菜品添加到 matched_dishes 列表中
                    matched_dishes.append(dish)

        #显示匹配的菜品
        # 遍历匹配的菜品
        for dish in matched_dishes:
            #创建一个新的按钮
            button = QPushButton(self.tab_all_dishes)
            #设置按钮文本，显示菜品名称和价格。
            button.setText(f"{dish['name']} - ¥{dish['price']:.2f}")
            #按钮的样式
            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: Microsoft YaHei;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            #将按钮的点击事件连接到 add_dish 方法
            button.clicked.connect(lambda checked, d=dish: self.add_dish(d))
            #将按钮添加到当前标签页的布局中
            self.tab_all_dishes.layout().addWidget(button)
        #切换到第一个标签页，显示搜索结果
        self.tabWidget.setCurrentIndex(0)
    #将菜品添加到订单中，如果不在则添加到订单中，在则添加数量
    def add_dish(self, dish):
        #遍历 self.selected_dishes 列表，检查当前菜品是否已在列表中
        for selected_dish in self.selected_dishes:
            #如果菜品已在列表中，增加其数量，并重新计算总价
            if selected_dish["name"] == dish["name"]:
                selected_dish["quantity"] += 1
                selected_dish["total_price"] = selected_dish["price"] * selected_dish["quantity"]
                break
        else:#如果菜品不在列表中，创建一个新的菜品字典，并将其添加到列表中
            new_dish = {
                "name": dish["name"],
                "price": dish["price"],
                "quantity": 1,
                "total_price": dish["price"]
            }
            self.selected_dishes.append(new_dish)
        #调用 update_selected_dishes_display 方法更新界面显示
        self.update_selected_dishes_display()


    #删除菜品
    def delete_dish(self, dish):
        #遍历 self.selected_dishes 列表，查找要删除的菜品。
        for i, selected_dish in enumerate(self.selected_dishes):
            #从当前订单中删除已选中的菜品
            if selected_dish["name"] == dish["name"]:
                del self.selected_dishes[i]
                break
        #更新刷新
        self.update_selected_dishes_display()

    #结账
    def checkout(self):
        #显示一个确认对话框，询问用户是否确定要结账。提供“是”和“否”两个选项，默认选中“否”。
        confirm = QMessageBox.question(
            self, "确认结账", "您确定要结账吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        #如果用户选择“否”，方法直接返回,不执行后续的操作
        if confirm != QMessageBox.StandardButton.Yes:
            return
        #检查；列表。如果没有则显示没有选择菜品方法返回
        try:
            if not self.selected_dishes:
                QMessageBox.information(self, "提示", "您还没有选择任何菜品！", QMessageBox.StandardButton.Ok)
                return

            #算所有选中菜品的总金额。
            total = sum(dish["price"] * dish["quantity"] for dish in self.selected_dishes)
            #序列化菜单信息
            menu_info = json.dumps(self.selected_dishes, ensure_ascii=False)

            # 保存订单到order_details表
            #保存的信息有table_name：当前餐桌的名称。username：当前登录的用户名total_amount：
            # 订单的总金额。menu_info：序列化后的菜单信息。checkout_time：当前时间，格式为 "%Y-%m-%d %H:%M:%S"。
            from database import add_order_to_details
            add_order_to_details(
                table_name=self.table_name,
                username=self.username,
                total_amount=total,
                menu_info=menu_info,
                checkout_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # 删除orders表中的订单信息
            from database import delete_order
            delete_order(self.table_name)
            #弹窗出弹窗显示信息，告知用户结账成功，并显示总金额。
            QMessageBox.information(self, "结账", f"总金额: ¥{total:.2f}\n结账成功！", QMessageBox.StandardButton.Ok)

            # 清空已选菜品并更新界面
            self.selected_dishes = []
            self.update_selected_dishes_display()

            # 更新餐桌状态为空闲
            from order_tables import update_table_status
            update_table_status(self.table_name, 0)

            # 返回到餐桌选择界面
            self.go_back_to_table_selection()
        #捕获并处理结账过程中可能出现的任何异常，显示错误消息框告知用户结账失败
        except Exception as e:
            QMessageBox.critical(self, "错误", f"结账失败: {str(e)}")

    def get_latest_order_id(self):
        with db_connection() as conn:
            cursor = conn.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]

    def save_order(self):
        if not self.selected_dishes:
            QMessageBox.information(self, "提示", "您还没有选择任何菜品！", QMessageBox.StandardButton.Ok)
            return

        try:
            total_amount = sum(dish["price"] * dish["quantity"] for dish in self.selected_dishes)
            # 确保中文正常序列化
            menu_info = json.dumps(self.selected_dishes, ensure_ascii=False)  # 添加 ensure_ascii=False
            order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with db_connection() as conn:
                # 提交事务
                conn.execute("DELETE FROM orders WHERE table_name=?", (self.table_name,))
                conn.execute(
                    "INSERT INTO orders (table_name, username, status, menu_info, total_amount, order_time) VALUES (?, ?, ?, ?, ?, ?)",
                    (self.table_name, self.username, 1, menu_info, total_amount, order_time)
                )
                conn.commit()  # 强制立即提交到数据库

            from order_tables import update_table_status
            update_table_status(self.table_name, 1)

            #直接更新界面
            self.update_selected_dishes_display()
            self.load_saved_order()  # 重新加载最新数据

            QMessageBox.information(self, "保存", "订单已保存！", QMessageBox.StandardButton.Ok)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"保存订单时发生数据库错误: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存订单时发生错误: {str(e)}")


    #用于删除餐桌的订单
    def delete_order(self):
        #从数据库中删除对应的订单
        #通过传递当前的餐桌名称
        from database import delete_order
        delete_order(self.table_name)

        #更新餐桌状态，调用 order_tables.update_table_status 函数，将当前餐桌的状态更新为 0（空闲状态）。
        from order_tables import update_table_status
        update_table_status(self.table_name, 0)


        #self.selected_dishes 列表清空
        self.selected_dishes = []
        self.update_selected_dishes_display()

        ## 显示删除成功的消息
        QMessageBox.information(self, "删除订单", "订单已删除！", QMessageBox.StandardButton.Ok)

    #切换全屏
    def toggle_fullscreen(self):
        # 检查是否是全屏模式
        if self.isFullScreen():
            self.showNormal()
            #更新按钮文本为“全屏”
            self.fullscreen_btn.setText("全屏")
        else:
            self.showFullScreen()
            #更新按钮文本为“退出全屏”
            self.fullscreen_btn.setText("退出全屏")

    #用于返回到餐桌择界面
    def go_back_to_table_selection(self):
        from order_tables import TableSelectionWindow
        # 创建餐桌选择窗口的界面
        self.table_selection_window = TableSelectionWindow(self.username)
        # 加载餐桌数据
        self.table_selection_window.load_tables()
        #显示餐桌选择界面
        self.table_selection_window.show()
        #关闭点餐窗口
        self.close()

    #加载并显示菜品
    def load_dishes(self):
        #代码遍历所有菜品标签页
        for tab in [self.tab_all_dishes, self.tab_cold_dishes, self.tab_hot_dishes, self.tab_drinks, self.tab_custom_dishes]:
            #while循环清理每个标签
            while tab.layout().count() > 0:#检查标签页的布局中是否还有控件
                item = tab.layout().takeAt(0)#取出第一个控件
                widget = item.widget()
                if widget:
                    widget.deleteLater()#将该控件在循环中去除
        # 获取当前标签页的分类
        current_tab_index = self.tabWidget.currentIndex()#获取当前选中的标签页索引
        tabs = ["全部", "冷菜", "热菜", "酒水", "其他"]#定义了几个标签
        category = tabs[current_tab_index]#根据当前标签页的索引（标签），获取对应的菜品分类

        #从数据库中获取菜品数据
        if category == "全部":
            #如果标签是全部，直接从数据库中获取所有菜品的数据
            with db_connection() as conn:
                cursor = conn.execute("SELECT name, price, category FROM dishes")
                # 将查询成果转换为列表
                dishes = [dict(name=row[0], price=row[1], category=row[2]) for row in cursor.fetchall()]
        #如果不是全部，则通过get_dishes_by_category方式获取指定分类的菜品列表。
        else:
            dishes = get_dishes_by_category(category)


        #创建菜品按钮并添加到标签页
        tab = [self.tab_all_dishes, self.tab_cold_dishes, self.tab_hot_dishes, self.tab_drinks, self.tab_custom_dishes][current_tab_index]
        #遍历dishes列表，为每个菜品创建一个按钮
        for dish in dishes:
            button = QPushButton(tab)
            #设置按钮文本，显示菜品名称和价格，价格保留两位小数。
            button.setText(f"{dish['name']} - ¥{dish['price']:.2f}")
            #样式
            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: Microsoft YaHei;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            #将按钮的点击事件连接到 self.add_dish(d) 方法，点击按钮时会将菜品添加到订单中。
            button.clicked.connect(lambda checked, d=dish: self.add_dish(d))
            #将按钮添加到标签页的布局中，使其在界面上显示
            tab.layout().addWidget(button)


