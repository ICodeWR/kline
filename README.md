# A股股票K线图

基于 Python Flask + PyEcharts 的 A 股股票 K 线图可视化网站，支持沪深两市股票搜索与历史 K 线展示。

## 功能特性

- **股票搜索**：支持按股票代码或名称模糊搜索，自动补全建议
- **K线图展示**：交互式 ECharts K 线图，支持缩放、拖拽
- **双数据源**：默认使用 akshare（免费开源），可选 tushare pro
- **响应式设计**：适配桌面端与移动端

## 技术栈

| 类别 | 技术 |
|------|------|
| Web 框架 | Flask |
| 前端 | Bootstrap + ECharts |
| 图表 | PyEcharts |
| 数据源 | akshare / tushare |
| 测试 | pytest + unittest |

## 项目结构

```
kline/
├── app.py                # Flask 主应用（路由、K线图生成）
├── stock_data.py         # 股票数据获取模块
├── requirements.txt      # 项目依赖
├── test_app.py           # Flask 应用单元测试
├── test_stock_data.py    # 数据模块单元测试
├── templates/
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   └── 404.html          # 错误页面
├── static/
│   └── css/
│       └── style.css     # 自定义样式
└── 教程.md               # 详细教程
```

## 快速开始

### 环境要求

- Python 3.8+

### 安装与运行

```bash
# 克隆仓库
git clone <repository-url>
cd kline

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

浏览器访问 `http://127.0.0.1:5000` 即可使用。

### 配置 tushare（可选）

akshare 默认可用，无需额外配置。如需使用 tushare pro：

1. 访问 [tushare.pro](https://tushare.pro) 注册并获取 token
2. 设置环境变量 `TUSHARE_TOKEN`：

```bash
# Windows:
set TUSHARE_TOKEN=your_token_here

# macOS / Linux:
export TUSHARE_TOKEN=your_token_here
```

## 运行测试

```bash
# 运行全部测试
python -m pytest test_stock_data.py test_app.py -v

# 仅运行数据模块测试
python -m pytest test_stock_data.py -v

# 仅运行 Flask 应用测试
python -m pytest test_app.py -v
```

## 数据源

| 数据源 | 特点 | 注册 |
|--------|------|------|
| **akshare**（默认） | 开源免费，开箱即用 | 无需 |
| **tushare** | 数据更全，需 token | 需要 |

## 许可证

[MIT License](LICENSE)