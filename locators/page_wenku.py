from selenium.webdriver.common.by import By

# 百度文库页面元素定位字典
baidu_page = {
    '__name__': '文件上传',
    '上传文件': (By.CLASS_NAME, 'add-new-btn'),
    '编辑': (By.CLASS_NAME, "el-button el-button--text el-button--small"),
    '弹窗文本大于20': (By.CLASS_NAME, 'dialog-message-body'),
    '全部提交': (By.XPATH, '//span[contains(text(),"全部提交")]'),
    '弹窗文本_正例': (By.CLASS_NAME, 'upload-success-title'),
    '弹窗文本_反例': (By.CLASS_NAME, 'dialog-message-body'),
    '提交后x按钮': (By.CLASS_NAME, 'upload-dialog-close')
}
