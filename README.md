# aliyunrds-to-n9e
获取所有阿里云上的RDS实例，并将性能数据推送至n9e监控平台

改自zabbix版：https://github.com/XWJR-Ops/zabbix-RDS-monitor  

``` 
pip3 install -r requirements.txt
```



~~改成一次 push 所有 matric 而不是单独循环 push,新增Redis指标获取 ~~ 