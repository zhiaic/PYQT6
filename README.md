# 基于PYQT6餐厅管理系统（前台）

基于PyQt6开发的桌面应用，用于管理餐厅的餐桌预订、菜品点单、订单处理及历史记录查询。支持多角色登录（管理员/普通员工），提供直观的图形化操作界面。

主要是给餐厅前台用的添加了很多的自定义。如餐桌添加和菜品添加。修修该改改应该能当酒店或者旅馆的代码用

## 主要功能

- **用户系统**
  - 登录/注册功能
  - 角色区分（管理员/普通员工）默认管理员账号:admin 密码：123456
  - 自动记录操作人员

- **餐桌管理** 
  - 实时状态显示（空闲/使用中/未结账）
  - 动态添加/删除餐桌
  - 全屏模式切换

- **菜品管理**
  - 分类展示（热菜/冷菜/酒水/其他）
  - 支持菜品增删改查
  - 智能搜索功能

- **订单系统** 
  - 可视化点餐界面
  - 订单暂存与修改
  - 结账功能与金额计算
  - 订单详情查看

- **历史记录** 
  - 按用户/日期/餐桌查询
  - 管理员查看全部订单
  - 订单详情导出展示

## 技术栈

- 前端框架: PyQt6
- 数据库: SQLite3
- 核心语言: Python 3.12+
- 数据序列化: JSON

## 快速开始

### 环境要求

```Py
 安装依赖
安装PyQt6和pyqt6-tools
pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyqt6-tools -i https://pypi.tuna.tsinghua.edu.cn/simple
```



#### 代码打包

```
pyinstaller --onefile --windowed --add-data "ui/*.ui:ui"  main.py
#main.py为文件名
```





#### 目录结构

```
/home directory
├── data/                 # 数据库文件
├── ui/                   # Qt Designer界面Ui文件
├── database.py           # 数据库操作模块
├── history_orders.py     # 历史订单模块
├── login_register.py     # 登录注册模块
├── main.py               # 程序入口
├── order_dishes.py       # 点餐界面模块
├── order_tables.py       # 餐桌管理模块
```



#### 一些吊话

```
#写这玩意一开始当用来着。好多地方看文档和问AI,好多地方不会，就挺西巴的。当pyqt6和python的学习了
后面再写个将数据可以同步到服务器的功能，然后可能再做用个web平台(基于php应该）。相对于做一个互联平台。然后可能做一个手机移端的?
```

