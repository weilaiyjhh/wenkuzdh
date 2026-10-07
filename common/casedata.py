import os, pandas
from common.log import log

project_path = os.path.dirname(os.path.dirname(__file__))  # 项目根目录


def read_casedata(xlsfile, columns=None, dtype=None):
    """
    功能：读取并处理用例数据
    参数：
        xlsfile：excel用例文件名（放在data目录下）
        columns：要读取的列名列表
        dtype：要转换数据类型的列名和类型字典
    返回值：二维用例列表 [[用例信息, 其余各列...], ...]
    注意：结果中已将"用例编号"和"用例标题"合并为"用例信息"，并删除了原列
    """
    xlsfile = os.path.join(project_path, 'data', xlsfile)
    try:
        data = pandas.read_excel(xlsfile, usecols=columns, dtype=dtype, keep_default_na=False)
        data['用例编号'] = data['用例编号'].astype(str)  # 转成字符串
        case_info = data['用例编号'] + '-' + data['用例标题']  # 拼接成 "编号-标题"
        data.insert(0, '用例信息', case_info)  # 插入到第一列
        del data['用例编号'], data['用例标题']  # 删除原始列
        cases = data.values.tolist()  # 转成二维列表
        log().info(f'读用例文件{xlsfile}')
        return cases
    except Exception as e:
        log().error(f'读用例文件{xlsfile}出错：{type(e)} {e}')
        exit()


if __name__ == '__main__':
    print(read_casedata('wenku.xlsx', ['用例编号', '用例标题', '上传文件路径', '上传文件名', '结果预期', '案例性质']))
