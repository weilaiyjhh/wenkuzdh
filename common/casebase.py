import unittest
from time import sleep
from common.conf import Conf
from common.log import log
from common.page import Page, screenshot


class BaseTestCase(unittest.TestCase, Page):
    """自动化测试用例基类，存放断言和测试固件（setUp/tearDown）"""

    @classmethod
    def setUpClass(cls):
        """所有用例前自动执行1次：打开浏览器，获取基础网址"""
        cls.open_browser()
        cls.url = Conf().get_baseurl()

    def setUp(self):
        """每条用例前自动执行1次：打开网页，初始化断言失败列表"""
        self.open_page(self.url)
        self.__failures = []  # 存放每条用例的断言失败消息

    def tearDown(self):
        """每条用例后自动执行1次：如果有断言失败则抛出异常"""
        self.raise_bugs()

    @classmethod
    def tearDownClass(cls):
        """所有用例后自动执行1次：退出浏览器"""
        cls.quit_browser()

    def check_equal(self, case_info, which_page, actual, expect):
        """
        功能：检查实际结果是否等于预期（使用 == 断言）
        参数：
            case_info：用例信息（编号-标题）
            which_page：检查哪个网页/步骤的描述
            actual：实际结果
            expect：预期结果
        注意：不要修改"截图文件已保存到{filename}"这句话，影响测试报告中的截图显示
        """
        sleep(1)
        if expect == actual:
            passed = True
        else:
            passed = False
        if passed:
            msg = f'{case_info}==={which_page}===结果比对通过'
            log().info(msg)
        else:
            filename = screenshot()
            msg = f'{case_info}==={which_page}===结果比对失败\n\t>>预期：{expect}\n\t>>实际：{actual}\n\t>>截图文件已保存到{filename}'
            self.__failures.append(msg.replace('\n\t', ''))
            log().warning(msg)

    def raise_bugs(self):
        """
        功能：如果有积累的断言失败，抛出AssertionError让unittest知道用例失败
        """
        if self.__failures:
            raise AssertionError(str("".join(self.__failures)))
