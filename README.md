# wenkuzdh — 百度文库自动化测试框架

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green)](https://www.selenium.dev/)
[![License](https://img.shields.io/badge/License-MIT-orange)]()

## 📖 简介

**wenkuzdh** 是一个基于 **Python + Selenium + unittest** 的 UI 自动化测试框架，主要用于 **百度文库（内部系统）** 的文件上传功能测试。

框架采用 **数据驱动测试（DDT）** 模式，测试用例数据存储在 Excel 文件中，通过分页操作封装、元素定位字典和统一断言机制，实现高复用、低维护成本的自动化测试。

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🧪 数据驱动测试 | 用例数据与代码分离，Excel 驱动，无需改代码即可新增用例 |
| 🌐 多浏览器支持 | 支持 Chrome / Firefox / Edge，配置文件一键切换 |
| 📝 HTML 测试报告 | 生成美观的 HTML 格式测试报告，包含截图和详细日志 |
| 📸 自动截图 | 断言失败时自动截取全屏并保存至 `screenshots/` 目录 |
| 🪵 日志系统 | 同时输出到控制台和日志文件，关键操作均被记录 |
| 📁 文件上传 | 支持通过 Windows 文件对话框上传单文件或多文件 |
| 🧩 PO 模式思想 | 页面元素定位集中管理（`locators/`），页面对象行为统一封装 |

## 📂 项目结构

```
wenkuzdh/
├── common/                  # 公共基础模块
│   ├── casebase.py          #    测试用例基类（断言、固件 setUp/tearDown）
│   ├── casedata.py          #    Excel 用例数据读取器
│   ├── conf.py              #    YAML 配置文件读取
│   ├── log.py               #    全局日志对象封装
│   ├── page.py              #    页面对象基类（浏览器操作、元素定位）
│   ├── WebHTMLTestRunner.py #    HTML 测试报告生成器
│   └── exception.py         #    自定义异常
├── conf/                    # 项目配置
│   └── server.yml           #    服务器地址 & 浏览器信息配置
├── data/                    # 测试数据
│   └── wenku.xlsx           #    Excel 用例数据表
├── drivers/                 # 浏览器驱动
│   └── chromedriver.exe     #    ChromeDriver（Chrome 使用）
├── locators/                # 页面元素定位字典
│   └── page_wenku.py        #    百度文库页面元素定义
├── testcase/                # 测试用例代码
│   ├── __init__.py
│   └── test_wenku.py        #    百度文库文件上传测试用例
├── runtest/                 # 测试运行入口
│   └── run.py               #    统一执行入口，生成测试报告
├── report/                  # 测试报告输出目录
├── screenshots/             # 断言失败自动截图存储目录
├── log/                     # 日志文件存储目录
│   └── wenku.log            #    运行时日志
├── logconf.ini              # 日志系统配置文件
└── README.md                # 本文件
```

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装以下依赖：

```bash
# Python >= 3.10
pip install selenium
pip install openpyxl      # 读取 Excel
pip install pandas
pip install PyYAML
pip install pillow         # 截图功能
pip install pywin32
pip install pywinauto
pip install ddt
```

### 2. 配置文件

编辑 `conf/server.yml`，设置目标环境和浏览器信息：

```yaml
browser_info:
  browser_name: chrome       # chrome / firefox / edge
  driver_file: chromedriver.exe
  user_data_dir: C:\Chrome\user   # Chrome 免登录用户数据目录（可选）

web_server:
  url: https://your-target-url.com  # 目标系统地址
```

> **提示**：如需 Chrome 免登录，请先手动登录一次目标网站，并将 `user_data_dir` 指向浏览器的用户数据目录。

### 3. 准备测试数据

在 `data/wenku.xlsx` 中按以下格式准备用例数据：

| 用例编号 | 用例标题 | 上传文件路径 | 上传文件名 | 结果预期 | 案例性质 |
|---------|---------|-------------|-----------|---------|---------|
| TC001 | 正常上传PDF | D:\files\test.pdf | test.pdf | 上传成功提示 | 正例 |
| TC002 | 上传超大文件 | D:\files\large.zip | large.zip | 上传失败提示 | 反例 |

### 4. 运行测试

#### 方式一：统一入口（推荐，生成 HTML 报告）

```bash
cd runtest
python run.py
```

测试报告将生成在 `report/wenku.html`。

#### 方式二：IDE 调试（方便逐行调试）

直接运行 `testcase/test_wenku.py`，可以在 IDE 中进行断点调试。

## 🔧 如何编写新用例

### 步骤 1：定义页面元素

在 `locators/page_*.py` 中添加新的元素定位：

```python
from selenium.webdriver.common.by import By

my_page = {
    '__name__': '我的页面',
    '登录按钮': (By.CSS_SELECTOR, '#login-btn'),
    '用户名输入框': (By.NAME, 'username'),
}
```

### 步骤 2：创建测试类

在 `testcase/` 下新建测试文件，继承 `BaseTestCase`：

```python
import unittest
from ddt import ddt, data, unpack
from common.casebase import BaseTestCase
from locators.page_mypage import my_page
from common.casedata import read_casedata

cases = read_casedata('mypage.xlsx', ['用例编号', '用例标题', ...])

@ddt
class MyTestCase(BaseTestCase):

    @data(*cases)
    @unpack
    def test_my_test(self, case_info, param1, expect):
        self.click(my_page, '登录按钮')
        result = self.get_text(my_page, '提示信息')
        self.check_equal(case_info, '登录结果', result, expect)

if __name__ == '__main__':
    loader = unittest.defaultTestLoader
    suite = loader.discover('.', 'test_mypage.py')
    report_file = open('../report/mypage.html', 'wb')
    runner = HTMLTestRunner(report_file, title='My Test Report', verbosity=2)
    runner.run(suite)
```

### 步骤 3：添加 Excel 数据

在 `data/` 下新建 Excel 文件，按照列名规范添加用例数据。

## 📊 测试报告示例

运行测试后生成的 HTML 报告包含：

- ✅ / ❌ 每条用例的执行状态
- 📝 详细的操作步骤日志
- 📸 失败用例的截图链接
- ⏱️ 总体耗时统计

## 🪲 常见问题

### Q: 启动浏览器时报错 "SessionNotCreatedException"？

A: 检查 ChromeDriver 版本是否与 Chrome 浏览器版本匹配，或者关闭所有已打开的 Chrome 窗口后重试。

### Q: 文件上传弹窗无法定位？

A: 确保浏览器不是最大化以外的窗口状态；如果是非 Chrome 浏览器，需调整 `page.py` 中的弹窗标题判断逻辑。

### Q: 如何切换浏览器？

A: 修改 `conf/server.yml` 中的 `browser_name` 字段为 `firefox` 或 `edge`，并放入对应的浏览器驱动。

## 🛠️ 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 编程语言 |
| Selenium | 4.x | 浏览器自动化 |
| unittest | 内置 | 测试框架 |
| ddt | latest | 数据驱动测试 |
| pandas | latest | Excel 数据处理 |
| PyYAML | latest | YAML 配置解析 |
| Pillow | latest | 屏幕截图 |
| pywinauto | latest | Windows 对话框交互 |
| pywin32 | latest | Windows API 调用 |

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

*Last updated: 2026-10-07*
