#coding=utf-8
"""
A TestRunner for use with the Python unit testing framework. It
generates a HTML report to show the result at a glance.
The simplest way to use this is to invoke its main method. E.g.
    import unittest
    import HTMLTestRunner
    ... define your tests ...
    if __name__ == '__main__':
        HTMLTestRunner.main()
For more customization options, instantiates a HTMLTestRunnerobject.
HTMLTestRunneris a counterpart to unittest's TextTestRunner. E.g.
    # output to a file
    fp = file('my_report.html', 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
                stream=fp,
                title='My unit test',
                description='This demonstrates the report output by HTMLTestRunner.'
                )
    # Use an external stylesheet.
    # See the Template_mixin class for more customizable options
    runner.STYLESHEET_TMPL = '<link rel="stylesheet" href="my_stylesheet.css" type="text/css">'
    # run the test
    runner.run(my_test_suite)
------------------------------------------------------------------------
Copyright (c) 2024, Keynes
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name Wai Yip Tung nor the names of its contributors may be
  used to endorse or promote products derived from this software without
  specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# URL: http://tungwaiyip.info/software/HTMLTestRunner.html

__author__ = "Keynes"
__version__ = "0.8.4"

import re
# TODO: color stderr
# TODO: simplify javascript using ,ore than 1 class in the class attribute?
import sys, logging, datetime, unittest
from io import StringIO
from xml.sax import saxutils

# ------------------------------------------------------------------------
# The redirectors below are used to capture output during testing. Output
# sent to sys.stdout and sys.stderr are automatically captured. However
# in some cases sys.stdout is already cached before HTMLTestRunner is
# invoked (e.g. calling logging.basicConfig). In order to capture those
# output, use the redirectors for the cached stream.
#
# e.g.
#   >>> logging.basicConfig(stream=HTMLTestRunner.stdout_redirector)
#   >>>

class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)

# ----------------------------------------------------------------------
# Template

class Template_mixin(object):
    """
    Define a HTML template for report customerization and generation.
    Overall structure of an HTML report
    HTML
    +------------------------+
    |<html>                  |
    |  <head>                |
    |                        |
    |   STYLESHEET           |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </head>               |
    |                        |
    |  <body>                |
    |                        |
    |   HEADING              |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   REPORT               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   ENDING               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </body>               |
    |</html>                 |
    +------------------------+
    """

    STATUS = {
        0: '通过',
        1: '失败',
        2: '错误',
    }

    # 对应STATUS 0，1，2
    BTN_STYLE_CLASS = {
        0: 'btn-success',
        1: 'btn-danger',
        2: 'btn-warning',
    }

    DEFAULT_TITLE = '测试报告标题'
    DEFAULT_DESCRIPTION = '测试描述'
    DEFAULT_TESTER = '测试员'

    RESULT = None

    # ------------------------------------------------------------------------
    # HTML Template

    HTML_TMPL = r"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>%(title)s</title>
    <meta name="generator" content="%(generator)s"/>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <link href="http://libs.baidu.com/bootstrap/3.0.3/css/bootstrap.min.css" rel="stylesheet">
    <script src="http://libs.baidu.com/jquery/2.0.0/jquery.min.js"></script>
    <script src="http://libs.baidu.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>
    %(stylesheet)s
</head>
<body >
%(heading)s
%(report)s
%(ending)s
<script language="javascript" type="text/javascript">
output_list = Array();
// 修改按钮颜色显示错误问题
$("button[id^='btn_pt']").addClass("btn btn-success");
$("button[id^='btn_ft']").addClass("btn btn-danger");
$("button[id^='btn_et']").addClass("btn btn-warning");
/*level
增加分类并调整，增加error按钮事件
0:Pass    //pt none, ft hiddenRow, et hiddenRow
1:Failed  //pt hiddenRow, ft none, et hiddenRow
2:Error    //pt hiddenRow, ft hiddenRow, et none
3:All     //pt none, ft none, et none
4:Summary //all hiddenRow
*/
//add Error button event
function showCase(level) {
    trs = document.getElementsByTagName("tr");
    for (var i = 0; i < trs.length; i++) {
        tr = trs[i];
        id = tr.id;
        if (id.substr(0,2) == 'ft') {
            if (level == 0 || level == 2 || level == 4 ) {
                tr.className = 'hiddenRow';
            }
            else {
                tr.className = '';
            }
        }
        if (id.substr(0,2) == 'pt') {
            if (level == 1 || level == 2 || level == 4) {
                tr.className = 'hiddenRow';
            }
            else {
                tr.className = '';
            }
        }
        if (id.substr(0,2) == 'et') {
            if (level == 0 || level == 1 || level == 4) {
                tr.className = 'hiddenRow';
            }
            else {
                tr.className = '';
            }
        }
    }
    //加入【展开】切换文字变化
    detail_class=document.getElementsByClassName('detail');
	//console.log(detail_class.length)
	if (level == 3) {
		for (var i = 0; i < detail_class.length; i++){
			detail_class[i].innerHTML="收起"
		}
	}
	else{
			for (var i = 0; i < detail_class.length; i++){
			detail_class[i].innerHTML="展开"
		}
	}
}
//add Error button event
function showClassDetail(cid, count) {
    var id_list = Array(count);
    var toHide = 1;
    for (var i = 0; i < count; i++) {
        tid0 = 't' + cid.substr(1) + '_' + (i+1);
        tid = 'f' + tid0;
        tr = document.getElementById(tid);
        if (!tr) {
            tid = 'p' + tid0;
            tr = document.getElementById(tid);
        }
        if (!tr) {
            tid = 'e' + tid0;
            tr = document.getElementById(tid);
        }
        id_list[i] = tid;
        if (tr.className) {
            toHide = 0;
        }
    }
    for (var i = 0; i < count; i++) {
        tid = id_list[i];
        //修改点击无法收起的BUG，加入【展开】切换文字变化
        if (toHide) {
            document.getElementById(tid).className = 'hiddenRow';
            document.getElementById(cid).innerText = "展开"
        }
        else {
            document.getElementById(tid).className = '';
            document.getElementById(cid).innerText = "收起"
        }
    }
}
function html_escape(s) {
    s = s.replace(/&/g,'&');
    s = s.replace(/</g,'<');
    s = s.replace(/>/g,'>');
    return s;
}
//添加圆饼图
function drawCircle(canvasId, data_arr, color_arr, text_arr) {
     var c = document.getElementById(canvasId);
     var ctx = c.getContext("2d");
     var radius = c.height / 2 - 20; //半径
     var ox = radius + 20,
         oy = radius + 20; //圆心
     var width = 10,
         height = 10; //图例宽和高
     var posX = ox * 2 + 20,
         posY = 30; //
     var textX = posX + width + 5,
         textY = posY + 10;
     var startAngle = 0; //起始弧度
     var endAngle = 0; //结束弧度
     for (var i = 0; i < data_arr.length; i++) {
         //绘制饼图
         endAngle = endAngle + data_arr[i] * Math.PI * 2; //结束弧度
         ctx.fillStyle = color_arr[i];
         ctx.beginPath();
         ctx.moveTo(ox, oy); //移动到到圆心
         ctx.arc(ox, oy, radius, startAngle, endAngle, false);
         ctx.closePath();
         ctx.fill();
         startAngle = endAngle; //设置起始弧度
         //绘制比例图及文字
         ctx.fillStyle = color_arr[i];
         ctx.fillRect(posX, posY + 30 * i, width, height);
         ctx.moveTo(posX, posY + 30 * i);
         ctx.font = 'bold 15px 微软雅黑'; //斜体 30像素 微软雅黑字体
         ctx.fillStyle = color_arr[i]; //"#000000";
         var percent = text_arr[i] + "：" + (100 * data_arr[i]).toFixed(2) + " %%";
         ctx.fillText(percent, textX, textY + 30 * i);
     }
 }
%(chart_script)s
 window.onload = init;

</script>
</body>
</html>
"""
    # variables: (title, generator, stylesheet, heading, report)

    # ------------------------------------------------------------------------
    # Stylesheet
    #
    # alternatively use a <link> for external style sheet, e.g.
    #   <link rel="stylesheet" href="$url" type="text/css">

    STYLESHEET_TMPL = """
<style type="text/css" media="screen">
body        { font-family: Microsoft YaHei,Tahoma,arial,helvetica,sans-serif;padding: 20px; font-size: 100%; }
table       { font-size: 100%; }
/* -- heading ---------------------------------------------------------------------- */
.heading {
    margin-top: 0ex;
    margin-bottom: 1ex;
    width: 50%;
    height: 230px;
    float: left;
}
.div_a {
    height:250x;
}
.div_r {
    width: 50%;
    height:230px;
    float: right;
    margin-bottom: 1ex;
    margin-top: 50px;
}
.attribute{
    font-size: 12px;
}
.heading .description {
    margin-top: 4ex;
    margin-bottom: 6ex;
}
/* -- report ------------------------------------------------------------------------ */
#total_row  { font-weight: bold; }
.passCase   { color: #228B22; font-size: 14px}
.failCase   { color: #d9534f; font-size: 14px}
.errorCase  { color: #f0ad4e; font-size: 14px}
.hiddenRow  { display: none; font-size: 14px}
.testcase   { margin-left: 2em; font-size: 14px}
</style>
"""

    # ------------------------------------------------------------------------
    # Heading
    #

    HEADING_TMPL = """<div class='div_a'>
<div class='heading'>
<h1 style="font-family: Microsoft YaHei">%(title)s</h1>
%(parameters)s
<!--p class='attribute'>%(description)s</p-->
</div>
<div class="div_r">
	<p>
    <canvas id="canvas_circle"></canvas>
</p>
</div>
</div>
""" # variables: (title, parameters, description)

    HEADING_ATTRIBUTE_TMPL = """<p class='attribute'><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%(name)s : </strong> %(value)s</p>
""" # variables: (name, value)

    # ------------------------------------------------------------------------
    # Report
    #
    # 汉化加美化效果
    REPORT_TMPL = """
<p id='show_detail_line'>
<a class="btn btn-info" href='javascript:showCase(3)'>展开全部{ %(count)s }</a>
<a class="btn btn-primary" href='javascript:showCase(4)'>折叠全部</a>
<a class="btn btn-success" href='javascript:showCase(0)'>通过{ %(Pass)s }</a>
<a class="btn btn-danger" href='javascript:showCase(1)'>失败{ %(fail)s }</a>
<a class="btn btn-warning" href='javascript:showCase(2)'>错误{ %(error)s }</a>
</p>
<table id='result_table' class="table table-condensed table-bordered table-hover" width="100%%">
<colgroup>
<col align='left' />
<col align='right' />
<col align='right' />
<col align='right' />
<col align='right' />
<col align='right' />
</colgroup>
<tr id='header_row' class="text-center active" style="font-weight: bold;font-size: 16px;">
    <td width="28%%">模块.类.测试用例</td>
    <td width="7%%">总计</td>
    <td width="7%%">通过</td>
    <td width="7%%">失败</td>
    <td width="7%%">错误</td>
    <td width="16%%">查看详情</td>
    <td width="28%%">截图</td>
</tr>
%(test_list)s
<tr id='total_row' class="text-center info attribute" style='font-size:14px'>
    <td width="28%%">统计</td>
    <td width="7%%">%(count)s</td>
    <td width="7%%">%(Pass)s</td>
    <td width="7%%">%(fail)s</td>
    <td width="7%%">%(error)s</td>
    <td width="16%%">通过率：%(passrate)s</td>
    <td width="28%%"><a href="" target="_blank"></a></td>
</tr>
</table>
""" # variables: (test_list, count, Pass, fail, error ,passrate)

    REPORT_CLASS_TMPL = r"""
<tr class='%(style)s' style="font-size:14px">
    <td width="28%%">%(desc)s</td>
    <td class="text-center" width="7%%">%(count)s</td>
    <td class="text-center" style="color:#228B22" width="7%%">%(Pass)s</td>
    <td class="text-center" style="color:#D2322D" width="7%%">%(fail)s</td>
    <td class="text-center" style="color:#FF8C00" width="7%%">%(error)s</td>
    <td class="text-center" width="16%%"><a href="javascript:showClassDetail('%(cid)s',%(count)s)" class="detail" id='%(cid)s'>展开</a></td>
	<td class="text-center" width="28%%">断言和错误截图</td>
</tr>
""" # variables: (style, desc, count, Pass, fail, error, cid)

    # 有output内容的样式，美化展示效果
    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s' width="28%%"><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center' width="44%%">
    <!--默认收起output信息
    <button id='btn_%(tid)s' type="button"  class="btn-xs collapsed" data-toggle="collapse" data-target='#div_%(tid)s'>%(status)s</button>
    <div id='div_%(tid)s' class="collapse">  -->
    <!-- 默认展开output信息-->
    <button id='btn_%(tid)s' type="button" class="btn-xs" data-toggle="collapse" data-target='#div_%(tid)s' style="font-size: 14px;">%(status)s</button>
    <div id='div_%(tid)s' class="collapse in">
    <pre style="text-align:left; font-size:14px">
    %(script)s
    </pre>
    </div>
    </td>
    <td align="right" width="28%%">
        %(image_links)s
    </td>
</tr>
""" # variables: (tid, Class, style, desc, status)

    # 无output内容样式改为button，按钮效果为不可点击
    REPORT_TEST_NO_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s' width="28%%"><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center' width="44%%"><button id='btn_%(tid)s' type="button"  class="btn-xs" disabled="disabled" data-toggle="collapse" data-target='#div_%(tid)s' style="font-size: 14px; background-color: #228B22">%(status)s</button></td>
	<td align="right" width="28%%">
	    %(image_links)s
    </td>
</tr>
""" # variables: (tid, Class, style, desc, status)

    REPORT_TEST_OUTPUT_TMPL = r"""
%(id)s%(output)s
""" # variables: (id, output)

    # ------------------------------------------------------------------------
    # ENDING
    #
    # 增加返回顶部按钮 
    ENDING_TMPL = """<div id='ending'> </div>
    <div style=" position:fixed;right:50px; bottom:30px; width:20px; height:20px;cursor:pointer">
    <a href="#"><span class="glyphicon glyphicon-eject" style = "font-size:30px;" aria-hidden="true">
    </span></a></div>
    """

    ECHARTS_SCRIPT = r"""
function init() {
     var text_arr = ["通过", "失败", "错误"];
     var color_arr = ["#5CB85C","#D2322D", "#F0AD4E"];
     var data_arr = [%(passa)r,%(faila)r,%(errora)r];
     drawCircle("canvas_circle", data_arr, color_arr, text_arr);
 }
"""
    # var data_arr = [%(passa)s,%(faila)s,%(errora)s];
    # var data_arr = [0.35,0.35,0.33];

# -------------------- The end of the Template class -------------------


TestResult = unittest.TestResult

class _TestResult(TestResult):
    # note: _TestResult is a pure representation of results.
    # It lacks the output and reporting ability compares to unittest._TextTestResult.

    def __init__(self, verbosity=1, retry=0, save_last_try=False):
        TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.verbosity = verbosity
        self.outputBuffer = StringIO()
        self.logger = logging.getLogger()
        self.retry = retry
        self.trys = 0
        self.status = 0
        self.save_last_try = save_last_try

        # result is a list of result in 4 tuple
        # (
        #   result code (0: success; 1: fail; 2: error),
        #   TestCase object,
        #   Test output (byte string),
        #   stack trace,
        # )
        self.result = []
        # 增加一个测试通过率
        self.passrate=float(0)

    def startTest(self, test):
        TestResult.startTest(self, test)
        # just one buffer for both stdout and stderr
        self.outputBuffer = StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector
        # 记录日志(含截图)到测试报告
        self.log_cap = StringIO()
        self.ch = logging.StreamHandler(self.log_cap)
        # self.ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)s] [%(levelname)s] %(message)s') # 需再次指定
        self.ch.setFormatter(formatter)
        self.logger.addHandler(self.ch)

    def complete_output(self):
        """
        Disconnect output redirection and return buffer.
        Safe to call multiple times.
        """
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        # return self.outputBuffer.getvalue()
        return self.outputBuffer.getvalue()+'\n'+self.log_cap.getvalue()

    def stopTest(self, test):
        # Usually one of addSuccess, addError or addFailure would have been called.
        # But there are some path in unittest that would bypass this.
        # We must disconnect stdout in stopTest(), which is guaranteed to be called.
		# 重新测试？2024/4/7
        # if self.retry and self.retry >= 1:
        #    if self.status == 1:
        #        self.trys += 1
        #        if self.trys <= self.retry:
        #            if self.save_last_try:
        #                t = self.result.pop(-1)
        #                if t[0] == 1:
        #                    self.failure_count -= 1
        #                else:
        #                    self.error_count -= 1
        #            test = copy.copy(test)
        #            sys.stderr.write("Retesting... ")
        #            sys.stderr.write(str(test))
        #            sys.stderr.write('..%d \n' % self.trys)
        #            doc = getattr(test, '_testMethodDoc', u"") or u''
        #            if doc.find('_retry') != -1:
        #                doc = doc[:doc.find('_retry')]
        #            desc = "%s_retry:%d" % (doc, self.trys)
        #            # if not PY3K:
        #            #     if isinstance(desc, str):
        #            #         desc = desc.decode("utf-8")
        #            test._testMethodDoc = desc
        #            test(self)
        #        else:
        #            self.status = 0
        #            self.trys = 0
        a=self.complete_output()
        # 清除log的handle
        self.logger.removeHandler(self.ch)
        return a

    def addSuccess(self, test):
        self.success_count += 1
        TestResult.addSuccess(self, test)
        output = self.complete_output()
        self.result.append((0, test, output, ''))
        if self.verbosity == 1:
            sys.stderr.write(str(test))
            sys.stderr.write(' OK\n')
        elif self.verbosity > 1:
            sys.stderr.write(str(test))
            sys.stderr.write(' PASSED\n')
        else:
            sys.stderr.write('.')

    def addError(self, test, err):
        self.error_count += 1
        TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str))
        if self.verbosity == 1:
            sys.stderr.write(str(test))
            sys.stderr.write(' E\n')
        elif self.verbosity > 1:
            sys.stderr.write(str(test))
            sys.stderr.write(' ERROR\n')
        else:
            sys.stderr.write('E')

    def addFailure(self, test, err):
        self.failure_count += 1
        TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str))
        if self.verbosity == 1:
            sys.stderr.write(str(test))
            sys.stderr.write(' F\n')
        elif self.verbosity > 1:
            sys.stderr.write(str(test))
            sys.stderr.write(' FAILED\n')
        else:
            sys.stderr.write('F')


class HTMLTestRunner(Template_mixin):
    def __init__(self, stream=sys.stdout, verbosity=1,title=None, description=None, tester=None):
        self.stream = stream
        self.verbosity = verbosity
        if title is None:
            self.title = self.DEFAULT_TITLE
        else:
            self.title = title
        if description is None:
            self.description = self.DEFAULT_DESCRIPTION
        else:
            self.description = description
        if tester is None:
            self.tester = self.DEFAULT_TESTER
        else:
            self.tester = tester
        self.startTime = datetime.datetime.now()

    def run(self, test):
        "Run the given test case or test suite."
        result = _TestResult(self.verbosity)
        test(result)
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        return result

    def sortResult(self, result_list):
        # unittest does not seems to run in any particular order.
        # Here at least we want to group them together by class.
        rmap = {}
        classes = []
        for n,t,o,e in result_list:
            cls = t.__class__
            if cls not in rmap:
                rmap[cls] = []
                classes.append(cls)
            rmap[cls].append((n,t,o,e))
        r = [(cls, rmap[cls]) for cls in classes]
        return r

    # 替换测试结果status为通过率
    def getReportAttributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        startTime = str(self.startTime)[:19]
        stopTime = str(self.stopTime)[:19]
        duration = str(self.stopTime - self.startTime)
        h, m, s=duration.split(':')
        total_seconds=round(int(h)*3600+int(m)*60+float(s), 2)
        duration=str(total_seconds)+'s'
        status = []
        status.append('共 %s 条用例' % (result.success_count + result.failure_count + result.error_count))
        if result.success_count: status.append('通过 %s' % result.success_count)
        if result.failure_count: status.append('失败 %s' % result.failure_count)
        if result.error_count: status.append('错误 %s' % result.error_count)
        if status:
            status = '，'.join(status)
            if (result.success_count + result.failure_count + result.error_count) > 0:
                self.passrate = str("%.2f%%" % (float(result.success_count) / float(result.success_count + result.failure_count + result.error_count) * 100))
            else:
                self.passrate = "0.00%"
        else:
            status = 'none'
        if result.error_count>0:
            sys.stderr.write(
                f'======================== {result.error_count} error in ')
        else:
            sys.stderr.write(f'======================== {result.failure_count} failed, {result.success_count} passed in ')
        sys.stderr.write(f'{duration} =========================\n')
        return [
            (u'测试人员', self.tester),
            (u'开始时间', startTime),
            (u'结束时间', stopTime),
            (u'总计耗时', duration),
            (u'测试结果', status + "，通过率 "+self.passrate),
            (u'测试环境', self.description),
        ]

    def generateReport(self, test, result):
        report_attrs = self.getReportAttributes(result)
        generator = 'HTMLTestRunner%s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        output = self.HTML_TMPL % dict(
            title = saxutils.escape(self.title),
            generator = generator,
            stylesheet = stylesheet,
            heading = heading,
            report = report,
            ending = ending,
            chart_script=self._generate_chart(result)
        )
        self.stream.write(output.encode('utf8'))

    def _generate_chart(self, result):
        self.alla=result.success_count+result.failure_count+result.error_count
        self.passa=result.success_count/self.alla
        self.faila=result.failure_count/self.alla
        self.errora=result.error_count/self.alla

        chart =r"""
function init() {
     var text_arr = ["通过", "失败", "错误"];
     var color_arr = ["#5CB85C","#D2322D", "#F0AD4E"];
     var data_arr = [%r,%r,%r];
     drawCircle("canvas_circle", data_arr, color_arr, text_arr);
 }
"""%(self.passa, self.faila, self.errora)
        return chart

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    # 增加Tester显示
    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                name = saxutils.escape(name),
                value = saxutils.escape(value),
            )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title = saxutils.escape(self.title),
            parameters = ''.join(a_lines),
            description = saxutils.escape(self.description),
            tester= saxutils.escape(self.tester),
        )
        return heading

    # 生成报告，添加注释
    def _generate_report(self, result):
        rows = []
        sortedResult = self.sortResult(result.result)
        for cid, (cls, cls_results) in enumerate(sortedResult):
            # subtotal for a class
            np = nf = ne = 0
            for n,t,o,e in cls_results:
                if n == 0: np += 1
                elif n == 1: nf += 1
                else: ne += 1

            # format class description
            if cls.__module__ == "__main__":
                name = cls.__name__
            else:
                name = "%s.%s" % (cls.__module__, cls.__name__)
            doc = cls.__doc__ and cls.__doc__.split("\n")[0] or ""
            desc = doc and '%s: %s' % (name, doc) or name
            row = self.REPORT_CLASS_TMPL % dict(
                style = ne > 0 and 'warning' or nf > 0 and 'danger' or 'success',
                desc = desc,
                count = np+nf+ne,
                Pass = np,
                fail = nf,
                error = ne,
                cid = 'c%s' % (cid+1),
            )
            rows.append(row)

            for tid, (n,t,o,e) in enumerate(cls_results):
                self._generate_report_test(rows, cid, tid, n, t, o, e)

        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
            count = str(result.success_count+result.failure_count+result.error_count),
            Pass = str(result.success_count),
            fail = str(result.failure_count),
            error = str(result.error_count),
            passrate =self.passrate,
        )
        return report

    def _generate_report_test(self, rows, cid, tid, n, t, o, e):
        # cid类序号从0开始下一个类增1，o输出的日志，e断言异常
        has_output = bool(o or e)
        tid = (n == 0 and 'p' or n == 1 and 'f' or 'e') + 't%s_%s' % (cid + 1, tid + 1) # tid测试序号从1开始，形如pt1_1、ft1_3
        tmp = tid.split('_')[1]  # 获得报告用例标题中的正确序号：1、2...
        no = '0' + tmp if len(tmp) < 2 else tmp
        name = t.id()
        if '___' in name:
            name = name.split('_'+no+'_')[0] + '_' + no # 修正报告用例标题中的编号从1开始，适用于ddt
        else:
            name = name.split('_' + str(int(tmp) - 1) + '_')[0] + '_' + no # 修正报告用例标题中的编号从1开始，适用于@parameterized.parameterized.expand
        doc = t.shortDescription() or ""
        desc = doc and ('%s: %s' % (name, doc)) or name
        tmpl = has_output and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL

        # o and e should be byte string because they are collected from stdout and stderr

        uo = o
        ue = e

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id = '',
            output = saxutils.escape(uo+ue).strip(),
        ) # id=''让网页中不显示ft、pt等文字

        # 插入截图
        start_key = '截图文件已保存到'
        end_key = '.png'
        unum = re.findall(f'{start_key}(.*?){end_key}', str(uo))
        if (uo or ue) and unum:
            images=[i + '.png' for i in unum]
            image_links ='&nbsp;<br><p>'
            for i in images:
                image_links=image_links+f'<a href="{i}"><img src="{i}" style="max-width: 100%; height: auto;"/></a><br><br>'
        else:
            image_links = '<a hidden="hidden" href=""><img src="" style="max-width: 100%; height: auto;"/></a>'

        row = tmpl % dict(
            tid=tid,
            Class=(n == 0 and 'hiddenRow' or 'none'),
            style=n == 2 and 'errorCase' or (n == 1 and 'failCase' or 'passCase'),
            desc=desc,
            script=script,
            image_links=image_links,
            btnclass=self.BTN_STYLE_CLASS[n],
            status=self.STATUS[n],
        )
        rows.append(row)
        if not has_output:
            return

    def _generate_ending(self):
        return self.ENDING_TMPL


##############################################################################
# Facilities for running tests from the command line
##############################################################################

# Note: Reuse unittest.TestProgram to launch test. In the future we may
# build our own launcher to support more specific command line
# parameters like test title, CSS, etc.
class TestProgram(unittest.TestProgram):
    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """
    def runTests(self):
        # Pick HTMLTestRunner as the default test runner.
        # base class's testRunner parameter is not useful because it means
        # we have to instantiate HTMLTestRunner before we know self.verbosity.
        if self.testRunner is None:
            self.testRunner = HTMLTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)

main = TestProgram

##############################################################################
# Executing this module from the command line
##############################################################################

if __name__ == "__main__":
    main(module=None)