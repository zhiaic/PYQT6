import sqlite3
from contextlib import contextmanager
from pathlib import Path
import datetime

# 数据库文件路径（自动创建data目录）
DB_PATH = Path("data/database.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在

#数据库连接管理器
#创建数据库
@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH)#连接数据库默认在data/database.db中
    try: #捕获异常
        #执行初始化
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role INTEGER NOT NULL DEFAULT 1  -- 0 为管理员，1 为普通用户
            );
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                status INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_details (
                id INTEGER PRIMARY KEY,
                table_name TEXT NOT NULL,
                username TEXT NOT NULL,
                total_amount REAL NOT NULL,
                menu_info TEXT NOT NULL,
                checkout_time TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS orders (
                "id" INTEGER NOT NULL,
                "table_name" TEXT NOT NULL,
                "username" TEXT NOT NULL,
                "total_amount" REAL NOT NULL,
                "order_time" TEXT NOT NULL,
                "status" TEXT NOT NULL,
                "checkout_time" TEXT NULL,
                "menu_info" TEXT NULL,
                PRIMARY KEY ("id")
            )
            ;


        ''')
        yield conn #在try快中，将连接对象传递给外部代码 如with db_connection() as conn:这样的调用
        conn.commit() #外部代码执行完毕后返回到这，然后执行 conn.comit提交数据库的变跟
    except Exception as e: #如果外部代码有异常触发该模块except
        conn.rollback() #撤销所有的提交变更
        print(f"数据库错误: {e}")
        raise
    finally:
        conn.close() #无论发生什么异常，最终关闭数据库，防止资源泄露


# ------------------------ 用户操作 ------------------------
def register_user(username: str, password: str) -> bool:
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
        return True
    except sqlite3.IntegrityError:
        return False

#调用数据库库查看账号和密码是否正确
def login_user(username: str, password: str) -> bool:
    with db_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM users WHERE username=? AND password=?",
            (username, password)
        )
        return bool(cursor.fetchone())


# ------------------------ 餐桌操作 ------------------------
def get_tables() -> list:
    with db_connection() as conn:
        cursor = conn.execute("SELECT name, status FROM tables")
        return [{"name": row[0], "status": row[1]} for row in cursor.fetchall()]


def add_table(name: str) -> bool:
    try:
        with db_connection() as conn:
            conn.execute("INSERT INTO tables (name) VALUES (?)", (name,))
            return True
    except sqlite3.IntegrityError:
        return False


def delete_table(table_name: str) -> bool:
    try:
        with db_connection() as conn:
            # 删除订单详情
            # conn.execute("DELETE FROM order_details WHERE order_id IN (SELECT id FROM orders WHERE table_name=?)", (table_name,))
            # 删除订单
            conn.execute("DELETE FROM orders WHERE table_name=?", (table_name,))
            # 删除餐桌
            cursor = conn.execute("DELETE FROM tables WHERE name=?", (table_name,))
            return cursor.rowcount > 0
    except Exception as e:
        print(f"删除餐桌时发生错误: {e}")
        return False

def update_table_status(table_name, new_status):
    with db_connection() as conn:
        conn.execute(
            "UPDATE tables SET status=? WHERE name=?",
            (new_status, table_name)
        )


# ------------------------ 菜品操作 ------------------------
def add_dish(name: str, price: float, category: str) -> bool:
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO dishes (name, price, category) VALUES (?, ?, ?)",
                (name, price, category)
            )
        return True
    except sqlite3.IntegrityError:
        return False


def delete_dish(name: str) -> bool:
    with db_connection() as conn:
        cursor = conn.execute("DELETE FROM dishes WHERE name=?", (name,))
        return cursor.rowcount > 0


def update_dish(name: str, new_price: float, new_category: str) -> bool:
    with db_connection() as conn:
        cursor = conn.execute(
            "UPDATE dishes SET price=?, category=? WHERE name=?",
            (new_price, new_category, name)
        )
        return cursor.rowcount > 0


def get_all_dishes() -> list:
    with db_connection() as conn:
        cursor = conn.execute("SELECT name, price, category FROM dishes")
        return [dict(name=row[0], price=row[1], category=row[2]) for row in cursor.fetchall()]


def get_dishes_by_category(category: str) -> list:
    with db_connection() as conn:
        cursor = conn.execute(
            "SELECT name, price FROM dishes WHERE category=?",
            (category,)
        )
        return [dict(name=row[0], price=row[1]) for row in cursor.fetchall()]


# -----------------------订单的数据库逻辑-----------------------------------
#add_order函数
def add_order(table_name, username, total_amount, menu_info, status=1):
    with db_connection() as conn:
        conn.execute("DELETE FROM orders WHERE table_name=?", (table_name,))
        order_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO orders (table_name, username, total_amount, menu_info, status, order_time) VALUES (?, ?, ?, ?, ?, ?)",
            (table_name, username, total_amount, menu_info, status, order_time)
        )
# update_order_status函数
def update_order_status(order_id, status, checkout_time=None):
    with db_connection() as conn:
        if checkout_time:
            conn.execute(
                "UPDATE orders SET status=?, checkout_time=? WHERE id=?",
                (status, checkout_time, order_id)
            )
        else:
            conn.execute(
                "UPDATE orders SET status=? WHERE id=?",
                (status, order_id)
            )

# delete_order函数
def delete_order(table_name):
    with db_connection() as conn:
        conn.execute("DELETE FROM orders WHERE table_name=?", (table_name,))

def get_orders_by_table(table_name):
    with db_connection() as conn:
        # 明确包含 menu_info 字段，并按时间倒序获取最新订单
        cursor = conn.execute(
            "SELECT id, table_name, username, total_amount, order_time, status, checkout_time, menu_info "
            "FROM orders WHERE table_name=? ORDER BY order_time DESC",  # 关键排序
            (table_name,)
        )
        orders = []
        for row in cursor.fetchall():
            orders.append({
                "id": row[0],
                "table_name": row[1],
                "username": row[2],
                "total_amount": row[3],
                "order_time": row[4],
                "status": row[5],
                "checkout_time": row[6],
                "menu_info": row[7]  # 确保对应 menu_info 列
            })
        return orders

def add_order_to_details(table_name, username, total_amount, menu_info,  checkout_time):
    with db_connection() as conn:
        conn.execute(
            "INSERT INTO order_details (table_name, username, total_amount, menu_info, checkout_time) VALUES (?, ?, ?, ?, ?)",
            (table_name, username, total_amount, menu_info, checkout_time)
        )

#菜品增删改
def get_all_dishes() -> list:
    """获取所有菜品信息"""
    with db_connection() as conn:
        cursor = conn.execute("SELECT id, name, price, category FROM dishes")
        return [dict(id=row[0], name=row[1], price=row[2], category=row[3]) for row in cursor.fetchall()]

def update_dish(dish_id: int, new_name: str, new_price: float, new_category: str) -> bool:
    """更新菜品信息"""
    try:
        with db_connection() as conn:
            cursor = conn.execute(
                "UPDATE dishes SET name=?, price=?, category=? WHERE id=?",
                (new_name, new_price, new_category, dish_id)
            )
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False  # 名称重复

def delete_dish(dish_id: int) -> bool:
    """删除菜品"""
    with db_connection() as conn:
        cursor = conn.execute("DELETE FROM dishes WHERE id=?", (dish_id,))
        return cursor.rowcount > 0

#
#获取历史订单

# def get_order_history_by_user(username: str) -> list:
#     with db_connection() as conn:
#         cursor = conn.execute(
#             "SELECT table_name, username, total_amount, menu_info, checkout_time "
#             "FROM order_details WHERE username=? ORDER BY checkout_time DESC",
#             (username,)
#         )
#         orders = []
#         for row in cursor.fetchall():
#             orders.append({
#                 "table_name": row[0],
#                 "username": row[1],
#                 "total_amount": row[2],
#                 "menu_info": row[3],
#                 "checkout_time": row[4]
#             })
#         return orders

def get_all_orders():
    """获取所有订单信息"""
    with db_connection() as conn:
        cursor = conn.execute(
            "SELECT table_name, username, total_amount, menu_info, checkout_time FROM order_details ORDER BY checkout_time DESC"
        )
        orders = []
        for row in cursor.fetchall():
            orders.append({
                "table_name": row[0],
                "username": row[1],
                "total_amount": row[2],
                "menu_info": row[3],
                "checkout_time": row[4]
            })
        return orders
#获取特定用户的历史订单信息
def get_order_history_by_user(username: str) -> list:
    with db_connection() as conn:
        cursor = conn.execute(
            "SELECT table_name, username, total_amount, menu_info, checkout_time FROM order_details WHERE username=? ORDER BY checkout_time DESC",
            (username,)
        )
        orders = []
        for row in cursor.fetchall():
            orders.append({
                "table_name": row[0],
                "username": row[1],
                "total_amount": row[2],
                "menu_info": row[3],
                "checkout_time": row[4]
            })
        return orders
#获取用户角色
def get_user_role(username):
    """获取用户角色"""
    with db_connection() as conn:
        cursor = conn.execute("SELECT role FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        if result:
            if result[0] == 0:
                return True
                # 管理员
            else:
                return False  # 普通用户
        else:
            return False  # 默认为普通用户

# 将测试代码严格限制在 __main__ 块内
if __name__ == "__main__":
    # 初始化测试数据
    with db_connection() as conn:
        # 清空所有表（仅用于测试）
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM tables")
        conn.execute("DELETE FROM dishes")
        conn.execute("DELETE FROM orders")
        conn.execute("DELETE FROM order_details")


    #测试用户功能
    print("注册 admin:", register_user("admin", "123456"))  # True
    print("重复注册:", register_user("admin", "123456"))    # False
    print("登录验证:", login_user("admin", "123456"))       # True

    # 测试餐桌功能
    print("添加餐桌A1:", add_table("A1"))  # True
    print("添加重复餐桌:", add_table("A1")) # False
    print("当前餐桌:", get_tables())
    print("删除餐桌:", delete_table('A1'))    # True

    # 测试菜品功能
    print("添加宫保鸡丁:", add_dish("宫保鸡丁", 32.0, "热菜"))  # True
    print("添加鱼香肉丝:", add_dish("鱼香肉丝", 30.0, "热菜"))  # True
    print("添加麻婆豆腐:", add_dish("麻婆豆腐", 28.0, "热菜"))  # True
    print("添加水煮肉片:", add_dish("水煮肉片", 45.0, "热菜"))  # True
    print("添加凉拌黄瓜:", add_dish("凉拌黄瓜", 18.0, "冷菜"))  # True
    print("添加凉拌海带:", add_dish("凉拌海带", 18.0, "冷菜"))  # True
    print("添加啤酒:", add_dish("啤酒", 8.0, "酒水"))  # True
    print("添加红酒:", add_dish("红酒", 128.0, "酒水"))  # True

    print("所有菜品:", get_all_dishes())
    print("热菜:", get_dishes_by_category("热菜"))
    print("冷菜:", get_dishes_by_category("冷菜"))
    print("酒水:", get_dishes_by_category("酒水"))

    # print("更新宫保鸡丁价格:", update_dish("宫保鸡丁", 35.0, "热菜"))  # True
    print("删除凉拌黄瓜:", delete_dish("凉拌黄瓜"))  # True

    print("餐巾纸:", add_dish("餐巾纸", 32.0, "其他"))  # True