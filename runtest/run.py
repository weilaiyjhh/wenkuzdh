import unittest
from common.WebHTMLTestRunner import HTMLTestRunner

loader = unittest.defaultTestLoader
suite = loader.discover('../testcase', '*test*.py')
report_name = '../report/wenku.html'
report_file = open(report_name, 'wb')
runner = HTMLTestRunner(report_file, title='wenku功能测试报告', description='报告环境描述', verbosity=2)
runner.run(suite)
