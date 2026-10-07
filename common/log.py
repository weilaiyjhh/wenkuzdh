import os, logging, logging.config

project_path = os.path.dirname(os.path.dirname(__file__))  # 拿到项目根目录
logging.config.fileConfig(os.path.join(project_path, 'logconf.ini'), encoding='utf-8')  # 加载日志配置文件

def log():
    """返回全局logger对象"""
    return logging.getLogger()

if __name__ == '__main__':
    log().debug('debug消息')
    log().info('info消息')
    log().warning('warning消息')
    log().error('error消息')
