import win32api
from datetime import datetime
from time import strftime, sleep
from PIL import ImageGrab
from pywinauto import Application, keyboard
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, SessionNotCreatedException, ElementNotInteractableException, InvalidElementStateException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from common.conf import Conf
from common.log import log
from common.exception import LocateException


def screenshot():
    """比对失败截图，截图保存为：项目/screenshots/日期_时间_毫秒.png"""
    try:
        sleep(2)
        origin = win32api.MonitorFromPoint((0, 0))
        monitor_info = win32api.GetMonitorInfo(origin)
        area = monitor_info.get("Work")
        image = ImageGrab.grab(area)
        now = datetime.now()
        milliseconds = now.microsecond // 1000
        now_time = strftime("%Y%m%d_%H%M%S") + f'_{milliseconds:03d}'
        filename = f'../screenshots/{now_time}.png'
        image.save(filename)
        return filename
    except Exception as e:
        log().error(f'截图出错：{type(e)} {e}')
        return None


class Page:
    """网页页面类，封装浏览器操作和元素定位方法"""

    @classmethod
    def open_browser(cls):
        """打开浏览器（支持chrome、firefox、edge）"""
        conf = Conf().get_browser_info()
        browser_name = conf['browser_name']
        user_data_dir = conf['user_data_dir']
        driver_file = conf['driver_file']
        try:
            if browser_name.lower() in ('chrome', 'google'):
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                opts = Options()
                opts.add_argument(f"user-data-dir={user_data_dir}")
                opts.add_experimental_option('detach', True)
                cls.browser = webdriver.Chrome(options=opts, service=Service(driver_file))
            elif browser_name.lower() == 'firefox':
                import warnings
                from selenium.webdriver.firefox.options import Options
                from selenium.webdriver.firefox.service import Service
                warnings.simplefilter('ignore', ResourceWarning)
                opts = Options()
                opts.profile = user_data_dir
                cls.browser = webdriver.Firefox(service=Service(log_path='nul'), options=opts)
            elif browser_name.lower() == 'edge':
                from selenium.webdriver.edge.options import Options
                from selenium.webdriver.edge.service import Service
                opts = Options()
                opts.add_experimental_option('detach', True)
                opts.add_argument(f"user-data-dir={user_data_dir}")
                cls.browser = webdriver.Edge(options=opts, service=Service(driver_file))
            else:
                log().error(f'不支持的浏览器：{browser_name}')
                exit()
            cls.browser.maximize_window()
            log().info(f'启动{browser_name}浏览器')
        except SessionNotCreatedException as e:
            log().error(f'启动浏览器出错：请关闭已打开的浏览器或检查驱动版本：{e}')
            exit()
        except Exception as e:
            log().error(f'启动浏览器出错：{type(e)} {e}')
            exit()

    def open_page(self, url, timeout=15):
        """打开网页，timeout秒没加载完则停止"""
        try:
            self.browser.set_page_load_timeout(timeout)
            self.browser.get(url)
            log().info(f'打开网址{url}')
        except TimeoutException:
            self.browser.execute_script('window.stop()')
            log().info(f'打开网址{url}超时{timeout}秒，停止加载')
        except Exception as e:
            log().error(f'打开网址{url}出错：{type(e)} {e}')
            exit()

    @classmethod
    def quit_browser(cls):
        """退出浏览器"""
        try:
            cls.browser.quit()
            log().info('退出浏览器')
        except Exception as e:
            log().error(f'退出浏览器出错：{e}')

    def __find_element(self, locator, condition='visibility', wait_seconds=None):
        """
        功能：定位元素（支持直接定位和显式等待）
        参数：
            locator：定位器元组 (By.XXX, '表达式')
            condition：等待条件，visibility/presence/clickable
            wait_seconds：显式等待秒数，默认None表示直接定位
        返回值：成功返回元素，失败返回LocateException
        """
        try:
            if wait_seconds:
                if condition == 'visibility':
                    e = WebDriverWait(self.browser, wait_seconds).until(
                        expected_conditions.visibility_of_element_located(locator))
                elif condition == 'presence':
                    e = WebDriverWait(self.browser, wait_seconds).until(
                        expected_conditions.presence_of_element_located(locator))
                elif condition == 'clickable':
                    e = WebDriverWait(self.browser, wait_seconds).until(
                        expected_conditions.element_to_be_clickable(locator))
                else:
                    return LocateException(f'不支持的等待条件：{condition}')
            else:
                e = self.browser.find_element(locator[0], locator[1])
            return e
        except Exception as ex:
            ee = str(ex)
            if 'Stacktrace' in ee:
                ee = ee[ee.index('Message:') + len('Message: '):ee.index('Stacktrace')]
            return LocateException(f'{type(ex)} {ee}')

    def click(self, page_dict, field, wait_seconds=None):
        """
        功能：点击页面元素
        参数：
            page_dict：页面定位字典
            field：字段名（字典中的键名）
            wait_seconds：显式等待秒数，默认不等待
        """
        try:
            msg = f'点击"{page_dict["__name__"]}"页面中的"{field}"'
            locator = page_dict[field]
            e = self.__find_element(locator, wait_seconds=wait_seconds)
            if type(e) == LocateException:
                log().error(f'{msg}出错：{locator}未定位到元素，可增加等待时间或改变定位方式')
                exit()
            else:
                e.click()
                log().info(msg)
        except (ElementNotInteractableException, InvalidElementStateException):
            log().error(f'{msg}出错：元素不能交互，可增加等待时间或改变定位方式')
            exit()
        except KeyError:
            log().error(f'{msg}出错：字段名{field}不存在')
            exit()
        except Exception as ex:
            log().error(f'{msg}出错：{type(ex)} {ex}')

    def get_text(self, page_dict, field, wait_seconds=None):
        """
        功能：获取元素的文本或value值
        参数：
            page_dict：页面定位字典
            field：字段名
            wait_seconds：显式等待秒数，默认不等待
        返回值：元素的文本或value值
        """
        try:
            msg = f'获取"{page_dict["__name__"]}"页面中"{field}"的文本'
            locator = page_dict[field]
            e = self.__find_element(locator, wait_seconds=wait_seconds)
            if type(e) == LocateException:
                log().error(f'{msg}出错：{locator}未定位到元素')
                return None
            else:
                if e.tag_name.lower() in ['input', 'select', 'textarea']:
                    text = e.get_attribute('value')
                else:
                    text = e.text
                log_text = '为空字符串' if text == '' else (None if text is None else f'为"{text}"')
                log().info(f'{msg}{log_text}')
                return text
        except KeyError:
            log().error(f'{msg}出错：字段名{field}不存在')
            return None
        except Exception as ex:
            log().error(f'{msg}出错：{type(ex)} {ex}')
            return None

    def upload(self, file_path, filenames):
        """
        功能：通过Windows文件对话框上传文件
        参数：
            file_path：文件所在目录的绝对路径
            filenames：单文件如'a.pdf'，多文件如'"a.pdf" "b.pdf"'
        """
        try:
            sleep(2)
            if isinstance(self.browser, webdriver.Chrome):
                title = '打开'
            else:
                title = '文件上传'
            app = Application().connect(title=title)
            win = app.window(title=title)
            fpath = win.child_window(class_name='ToolbarWindow32', found_index=2)
            fpath.click()
            keyboard.send_keys(f'{file_path}', with_spaces=True)
            keyboard.send_keys('{ENTER}')
            txt = win.child_window(class_name='Edit', found_index=0)
            sleep(1)
            txt.set_text(filenames)
            btn = win.child_window(class_name='Button', title="打开(&O)")
            sleep(1)
            btn.set_focus()
            btn.click()
            log().info(f'上传文件{file_path}/{filenames}完成')
        except Exception as e:
            log().error(f'上传文件{file_path}/{filenames}出错：{type(e)} {e}')
            exit()

    def quit_browser(cls):
        """退出浏览器"""
        try:
            cls.browser.quit()
            log().info('退出浏览器')
        except Exception as e:
            log().error(f'退出浏览器出错：{e}')
