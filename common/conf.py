import os, yaml
from common.log import log

project_path = os.path.dirname(os.path.dirname(__file__))  # 项目根目录


class Conf:
    """配置类：读取yaml配置文件，提供基础网址和浏览器信息"""

    def __init__(self):
        """读配置文件到成员变量中"""
        filename = os.path.join(project_path, 'conf', 'server.yml')
        try:
            with open(filename, encoding='utf-8') as confile:
                self.__conf = yaml.load(confile, Loader=yaml.FullLoader)
            log().info(f'读服务器配置文件{filename}：{self.__conf}')
        except Exception as e:
            log().error(f'读服务器配置文件{filename}出错：{type(e)} {e}')
            exit()

    def get_baseurl(self):
        """
        功能：获得基础网址
        返回值：基础网址字符串
        """
        try:
            base_url = self.__conf['web_server']['url']
            log().info(f'获取基础网址：{base_url}')
            return base_url
        except Exception as e:
            log().error(f'获取基础网址出错：{type(e)} {e}')
            exit()

    def get_browser_info(self):
        """
        功能：获得浏览器信息
        返回值：浏览器信息字典，包含浏览器名称、用户数据目录、驱动文件路径
        """
        try:
            browser_info = self.__conf['browser_info']
            # 拼接驱动文件的绝对路径
            browser_info['driver_file'] = os.path.join(
                project_path, 'drivers', browser_info['driver_file']
            )
            # 只保留需要的字段
            result = {
                'browser_name': browser_info['browser_name'],
                'user_data_dir': browser_info['user_data_dir'],
                'driver_file': browser_info['driver_file'],
            }
            log().info(f'本次测试使用的浏览器信息：{result}')
            return result
        except Exception as e:
            log().error(f'获取浏览器信息出错：{type(e)} {e}')
            exit()


if __name__ == '__main__':
    a = Conf()
    print(a.get_baseurl())
    print(a.get_browser_info())
