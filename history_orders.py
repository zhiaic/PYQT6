from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QPushButton, QMessageBox, QTableWidget, QLineEdit, QComboBox
from PyQt6 import uic
from database import get_user_role, get_all_orders, get_order_history_by_user
import json

class HistoryOrdersWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"历史订单记录 - 用户: {username}")
        uic.loadUi("ui/history_order.ui", self)

        # 使用 findChild 获取控件
        self.back_btn = self.findChild(QPushButton, "back_btn")
        self.search_box = self.findChild(QLineEdit, "search_box")
        self.filter_combo = self.findChild(QComboBox, "filter_combo")
        self.order_table = self.findChild(QTableWidget, "order_table")

        # 绑定事件
        self.back_btn.clicked.connect(self.close)
        self.search_box.textChanged.connect(self.filter_orders)
        self.filter_combo.currentIndexChanged.connect(self.filter_orders)
        self.order_table.itemDoubleClicked.connect(self.show_order_details)

        self.load_orders()
    #加载订单数据
    def load_orders(self):
        #判断是否为管理员
        is_admin = get_user_role(self.username)
        if is_admin:
            #如果是管理员则获取全部订单
            self.orders = get_all_orders()
        else:
            #如果非管理员则只有自己的订单
            self.orders = get_order_history_by_user(self.username)
        #确保表格的行数与订单数据的数量一致
        #self.order_table：当前窗口中的一个 QTableWidget 控件，用于显示订单数据。setRowCount：设置表格的行数
        #len(self.orders)：获取订单数据列表的长度，即订单的数量
        self.order_table.setRowCount(len(self.orders))
        #遍历订单数据并填充表格
            #row 是当前行号，order 是订单的字典
        for row, order in enumerate(self.orders):
            #QTableWidgetItem(value)创建一个表格项，显示文本
            #str(row + 1)行号+1往后哦订单号
            self.order_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            #table_name获取餐桌号
            self.order_table.setItem(row, 1, QTableWidgetItem(order['table_name']))
            #金额
            self.order_table.setItem(row, 2, QTableWidgetItem(f"¥{order['total_amount']:.2f}"))
            #结账时间
            self.order_table.setItem(row, 3, QTableWidgetItem(order['checkout_time']))
            #创建个按钮显示详细
            details_btn = QPushButton("详情")
            #绑定按钮的点击事件到 show_order_details 方法
            details_btn.clicked.connect(lambda checked, r=row: self.show_order_details(r))
            #在五行中放按钮
            self.order_table.setCellWidget(row, 4, details_btn)
        #自动调整列宽
        self.order_table.resizeColumnsToContents()
    #根据条件过滤订单搜索框
    def filter_orders(self):
        search_text = self.search_box.text().strip().lower()
        filter_index = self.filter_combo.currentIndex()

        for row in range(self.order_table.rowCount()):
            if row < len(self.orders):
                order = self.orders[row]
                if filter_index == 0:  # 全部
                    condition = (search_text in str(row + 1).lower() or
                                 search_text in order['checkout_time'].lower() or
                                 search_text in order['table_name'].lower())
                    self.order_table.setRowHidden(row, not condition)
                elif filter_index == 1:  # 按日期
                    self.order_table.setRowHidden(row, search_text not in order['checkout_time'].lower())
                elif filter_index == 2:  # 按餐桌
                    self.order_table.setRowHidden(row, search_text not in order['table_name'].lower())
            else:
                self.order_table.setRowHidden(row, True)
    #显示订单详情
    def show_order_details(self, row=None):
        if row is None:
            row = self.order_table.currentRow()

        if 0 <= row < len(self.orders):
            order = self.orders[row]
            details = json.loads(order['menu_info'])

            details_text = (f"桌号: {order['table_name']}\n"
                            f"结账时间: {order['checkout_time']}\n"
                            f"总金额: ¥{order['total_amount']:.2f}\n\n"
                            "菜单详情:\n")
            for item in details:
                details_text += f"- {item['name']} x{item['quantity']} - ¥{item['total_price']:.2f}\n"

            QMessageBox.information(self, "订单详情", details_text)