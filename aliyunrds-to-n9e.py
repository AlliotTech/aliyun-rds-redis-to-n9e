#!/bin/env python3

from aliyunsdkcore import client
from aliyunsdkrds.request.v20140815 import DescribeDBInstancesRequest, DescribeDBInstancePerformanceRequest, DescribeResourceUsageRequest
import json
import requests
from time import time
import datetime

# 阿里云秘钥
ID = 'xxx'
Secret = 'xxx'
# 区域
RegionID = 'cn-shenzhen'

# n9e token 在个人设置中
N9eToken = 'xxx'
# n9e 地址
N9eUrl = 'n9e.com'
Step = 30

RdsMetrics = ["MySQL_NetworkTraffic_In", "MySQL_NetworkTraffic_Out", "MySQL_QPS", "MySQL_TPS", "MySQL_Sessions_Active",
              "MySQL_Sessions_Totle", "ibuf_read_hit", "ibuf_use_ratio", "ibuf_dirty_ratio", "inno_data_read",
              "inno_data_written", "ibuf_request_r", "ibuf_request_w", "Innodb_log_write_requests", "Innodb_log_writes",
              "Innodb_os_log_fsyncs", "tb_tmp_disk", "Key_usage_ratio", "Key_read_hit_ratio", "Key_write_hit_ratio",
              "myisam_keyr_r", "myisam_keyr_w", "myisam_keyr", "myisam_keyw", "com_delete", "com_insert",
              "com_insert_select", "com_replace", "com_replace_select", "com_select", "com_update", "inno_row_readed",
              "inno_row_update", "inno_row_delete", "inno_row_insert", "Inno_log_writes", "cpuusage", "memusage", "io",
              "ins_size", "data_size", "log_size", "tmp_size", "other_size"
              ]

'''
获取 阿里 RDS 列表
'''


def GetRdsList():
    AcsClient = client.AcsClient(ID, Secret, RegionID)
    RdsRequest = DescribeDBInstancesRequest.DescribeDBInstancesRequest()
    RdsRequest.set_accept_format('json')
    RdsInfo = AcsClient.do_action_with_exception(RdsRequest)
    return RdsInfo


'''
添加设备到 n9e 中
ip:    IP地址
ident: 英文标识
name:  名称
'''


def AddDeviceToN9e(ip, ident, name):
    url = "http://" + N9eUrl + "/api/ams-ce/hosts"
    payload = "[\"% s::% s::% s\"]" % (ip, ident, name)
    headers = {
        'Connection': 'keep-alive',
        'DNT': '1',
        'content-type': 'application/json',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'X-User-Token': N9eToken
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=payload.encode())
    print(payload)
    print(response.text)


'''
上报数据到 n9e
Endpoint: 一般为 IP
RegionID: 地区ID: cn-shenzhen
Metric:   指标名
Value:    指标值
Step:     上报频率
'''


def UpdateData(Endpoint, RegionID, Metric, Value, Step):
    url = "http://" + N9eUrl + ":2080/v1/push"
    data = [
        {
            "endpoint": Endpoint,
            "metric": Metric,
            "tagsMap": {
                "Region": RegionID
            },
            "value": float(Value),
            "timestamp": int(time()),
            "step": int(Step)
        }
    ]
    res = requests.post(url, json=data)
    print(data)
    print(res.text)


'''
获取 实例对应的性能数据
DBInstanceId： 实例ID
Key：          键
'''


def GetRdsValue(DBInstanceId, Key):
    def GetPerformance(DBInstanceId, MasterKey, IndexNum):
        '''
        阿里云返回的数据为 UTC 时间，因此要转换为东八区时间。其他时区同理。
        最小时间间隔为 1 分钟，因此这里选择时间跨度为 1 分钟
        '''
        AcsClient = client.AcsClient(ID, Secret, RegionID)
        UTC_End = datetime.datetime.today() - datetime.timedelta(hours=8)
        UTC_Start = UTC_End - datetime.timedelta(minutes=1)
        StartTime = datetime.datetime.strftime(UTC_Start, '%Y-%m-%dT%H:%MZ')
        EndTime = datetime.datetime.strftime(UTC_End, '%Y-%m-%dT%H:%MZ')
        Performance = DescribeDBInstancePerformanceRequest.DescribeDBInstancePerformanceRequest()
        Performance.set_accept_format('json')
        Performance.set_DBInstanceId(DBInstanceId)
        Performance.set_Key(MasterKey)
        Performance.set_StartTime(StartTime)
        Performance.set_EndTime(EndTime)
        PerformanceInfo = AcsClient.do_action_with_exception(Performance)
        Info = json.loads(PerformanceInfo)
        Value = Info['PerformanceKeys']['PerformanceKey'][0]['Values']['PerformanceValue'][-1]['Value']
        return (str(Value).split('&')[IndexNum])
    if (Key == "MySQL_NetworkTraffic_In"):
        IndexNum = 0
        MasterKey = "MySQL_NetworkTraffic"
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒钟的输出流量
    elif (Key == "MySQL_NetworkTraffic_Out"):
        IndexNum = 1
        MasterKey = "MySQL_NetworkTraffic"
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 每秒SQL语句执行次数
    elif (Key == "MySQL_QPS"):
        IndexNum = 0
        MasterKey = "MySQL_QPSTPS"
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒事务数
    elif (Key == "MySQL_TPS"):
        IndexNum = 1
        MasterKey = "MySQL_QPSTPS"
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 当前活跃连接数
    elif (Key == "MySQL_Sessions_Active"):
        MasterKey = "MySQL_Sessions"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 当前总连接数
    elif (Key == "MySQL_Sessions_Totle"):
        MasterKey = "MySQL_Sessions"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # InnoDB缓冲池的读命中率
    elif (Key == "ibuf_read_hit"):
        MasterKey = "MySQL_InnoDBBufferRatio"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # InnoDB缓冲池的利用率
    elif (Key == "ibuf_use_ratio"):
        MasterKey = "MySQL_InnoDBBufferRatio"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # InnoDB缓冲池脏块的百分率
    elif (Key == "ibuf_dirty_ratio"):
        MasterKey = "MySQL_InnoDBBufferRatio"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # InnoDB平均每秒钟读取的数据量
    elif (Key == "inno_data_read"):
        MasterKey = "MySQL_InnoDBDataReadWriten"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # InnoDB平均每秒钟写入的数据量
    elif (Key == "inno_data_written"):
        MasterKey = "MySQL_InnoDBDataReadWriten"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒向InnoDB缓冲池的读次数
    elif (Key == "ibuf_request_r"):
        MasterKey = "MySQL_InnoDBLogRequests"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒向InnoDB缓冲池的写次数
    elif (Key == "ibuf_request_w"):
        MasterKey = "MySQL_InnoDBLogRequests"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒日志写请求数
    elif (Key == "Innodb_log_write_requests"):
        MasterKey = "MySQL_InnoDBLogWrites"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒向日志文件的物理写次数
    elif (Key == "Innodb_log_writes"):
        MasterKey = "MySQL_InnoDBLogWrites"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒向日志文件完成的fsync()写数量
    elif (Key == "Innodb_os_log_fsyncs"):
        MasterKey = "MySQL_InnoDBLogWrites"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MySQL执行语句时在硬盘上自动创建的临时表的数量
    elif (Key == "tb_tmp_disk"):
        MasterKey = "MySQL_TempDiskTableCreates"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒Key Buffer利用率
    elif (Key == "Key_usage_ratio"):
        MasterKey = "MySQL_MyISAMKeyBufferRatio"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒Key Buffer读命中率
    elif (Key == "Key_read_hit_ratio"):
        MasterKey = "MySQL_MyISAMKeyBufferRatio"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒Key Buffer写命中率
    elif (Key == "Key_write_hit_ratio"):
        MasterKey = "MySQL_MyISAMKeyBufferRatio"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒钟从缓冲池中的读取次数
    elif (Key == "myisam_keyr_r"):
        MasterKey = "MySQL_MyISAMKeyReadWrites"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒钟从缓冲池中的写入次数
    elif (Key == "myisam_keyr_w"):
        MasterKey = "MySQL_MyISAMKeyReadWrites"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒钟从硬盘上读取的次数
    elif (Key == "myisam_keyr"):
        MasterKey = "MySQL_MyISAMKeyReadWrites"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MyISAM平均每秒钟从硬盘上写入的次数
    elif (Key == "myisam_keyw"):
        MasterKey = "MySQL_MyISAMKeyReadWrites"
        IndexNum = 3
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Delete语句执行次数
    elif (Key == "com_delete"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Insert语句执行次数
    elif (Key == "com_insert"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Insert_Select语句执行次数
    elif (Key == "com_insert_select"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Replace语句执行次数
    elif (Key == "com_replace"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 3
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Replace_Select语句执行次数
    elif (Key == "com_replace_select"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 4
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Select语句执行次数
    elif (Key == "com_select"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 5
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒Update语句执行次数
    elif (Key == "com_update"):
        MasterKey = "MySQL_COMDML"
        IndexNum = 6
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒从InnoDB表读取的行数
    elif (Key == "inno_row_readed"):
        MasterKey = "MySQL_RowDML"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒从InnoDB表更新的行数
    elif (Key == "inno_row_update"):
        MasterKey = "MySQL_RowDML"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒从InnoDB表删除的行数
    elif (Key == "inno_row_delete"):
        MasterKey = "MySQL_RowDML"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒从InnoDB表插入的行数
    elif (Key == "inno_row_insert"):
        MasterKey = "MySQL_RowDML"
        IndexNum = 3
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # 平均每秒向日志文件的物理写次数
    elif (Key == "Inno_log_writes"):
        MasterKey = "MySQL_RowDML"
        IndexNum = 4
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MySQL实例CPU使用率(占操作系统总数)
    elif (Key == "cpuusage"):
        MasterKey = "MySQL_MemCpuUsage"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MySQL实例内存使用率(占操作系统总数)
    elif (Key == "memusage"):
        MasterKey = "MySQL_MemCpuUsage"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # MySQL实例的IOPS（每秒IO请求次数）
    elif (Key == "io"):
        MasterKey = "MySQL_IOPS"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # ins_size实例总空间使用量
    elif (Key == "ins_size"):
        MasterKey = "MySQL_DetailedSpaceUsage"
        IndexNum = 0
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # data_size数据空间
    elif (Key == "data_size"):
        MasterKey = "MySQL_DetailedSpaceUsage"
        IndexNum = 1
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # log_size日志空间
    elif (Key == "log_size"):
        MasterKey = "MySQL_DetailedSpaceUsage"
        IndexNum = 2
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # tmp_size临时空间
    elif (Key == "tmp_size"):
        MasterKey = "MySQL_DetailedSpaceUsage"
        IndexNum = 3
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a

    # other_size系统空间
    elif (Key == "other_size"):
        MasterKey = "MySQL_DetailedSpaceUsage"
        IndexNum = 4
        a = GetPerformance(DBInstanceId, MasterKey, IndexNum)
        return a


if __name__ == '__main__':
    RdsInfo = GetRdsList()
    for RdsInfoJson in (json.loads(RdsInfo))['Items']['DBInstance']:
        try:
            # 如果需要添加所有实例进 N9e 请取消注释。
            # AddDeviceToN9e(
            #     'rds-' + RdsInfoJson['DBInstanceId'],
            #     'rds-' + RdsInfoJson['DBInstanceId'],
            #     RdsInfoJson['DBInstanceDescription'])
            for i in RdsMetrics:
                UpdateData(
                    'rds-' +
                    RdsInfoJson['DBInstanceId'],
                    RegionID,
                    i,
                    GetRdsValue(
                        RdsInfoJson['DBInstanceId'],
                        i),
                    Step)
        except Exception as e:
            print(Exception, ":", e)
