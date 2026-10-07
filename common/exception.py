class LocateException(Exception):
    """自定义异常，统一各种定位错误"""
    def __init__(self, message):
        if 'Stacktrace' in message:
            message = message[message.index('Message:')+len('Message: '):message.index('Stacktrace')]
        self.message = message.strip()

    def __str__(self):
        return f"出错: {self.message}"
