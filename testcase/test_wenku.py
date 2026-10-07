import unittest
from time import sleep
from ddt import ddt, data, unpack
from common.WebHTMLTestRunner import HTMLTestRunner
from common.casebase import BaseTestCase
from locators.page_wenku import baidu_page
from common.casedata import read_casedata

cases=read_casedata('wenku.xlsx', ['用例编号','用例标题', '上传文件路径', '上传文件名',  '结果预期','案例性质'])

#cases=[cases[0]]
#print(cases)
@ddt##ddt意思是数据驱动测试
class Wenku(BaseTestCase): #右击执行方便调试，但不生成测试报告D:\OneDrive\桌面\百度文库

    @data(*cases)###这里*cases是对cases解包，也就是变成了cases[0]，cases[1]这种。把cases里的全部解包出来。data就让cases进行循环
    @unpack###解包，就在cases里拿第一条出来进行解包，再把数值分别给test_calc里的各个
    def test_wenku(self, case_info, case_wjlj, case_wjm, yuqi, case_al):
        if ';' in case_wjm:  # 表示多文件
            names = [name.strip() for name in case_wjm.split(';') if name.strip()]
            # 每个文件名加双引号，空格拼接
            case_wjm1 = ' '.join(f'"{name}"' for name in names)
        else:
            case_wjm1 = case_wjm
        sleep(4)
        self.click(baidu_page,'上传文件')
        sleep(4)
        self.upload(case_wjlj,case_wjm1)
        sleep(7)
        yuqi1 = yuqi
        self.click(baidu_page,'全部提交')
        sleep(3)
        locator_key='弹窗文本_正例' if case_al=='正例' else '弹窗文本_反例'
        shiji=self.get_text(baidu_page,locator_key)
        self.check_equal(case_info,'上传提交后，检查是否成功与否',shiji,yuqi1)
if __name__=='__main__': #右击执行方便调试代码，但不生成报告，不写下面的代码，用菜单执行也不生成报告
    loader = unittest.defaultTestLoader###测试加载器
    suite = loader.discover('../testcase', 'test_wenku.py')
    report_file = open('../report/web_calc.html', 'wb')
    runner = HTMLTestRunner(report_file, title='wenku功能测试报告', description='报告环境描述', verbosity=2)
    runner.run(suite)
