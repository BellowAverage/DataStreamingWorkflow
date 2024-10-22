# Nginx Access.log Generator

Created: September 12, 2024 1:48 PM
Labels & Language: Python, http, nginx

## 引言

Nginx是一种流行的开源Web服务器和反向代理服务器技术。它旨在处理高流量的网站并快速高效地提供Web内容。Nginx还可用作负载均衡器、HTTP缓存和电子邮件协议（IMAP、POP3和SMTP）的代理服务器等。本篇笔记记录的技术，旨在通过模拟多个IP登录访问nginx的`index.html`页面，达到生成数量级达到至多每日千万体量的访问日志的效果。这些日志文件数据将作为后续分析的基础。

## Nginx生成访问日志

### 程序设计概述

考虑项目的性质和成本，将采用nginx架构的django项目部署在本地虚拟机中，模拟公网中建立的网站（实际在内网进行操作），该虚拟机服务器采用Ubuntu Linux操作系统。搭载Windows系统的本地主机作为发起访问请求的实体，通过`python requests`库编写的自动脚本，实现千万数量级的访问操作。在这个自动脚本中，除了本机访问外，为了模拟多个虚拟`IP`，使用基于`squid`的`proxy`代理技术，通过另外3台配置有`squid`代理的由虚拟机模拟的服务器（分别名为`hadoop102`, `hadoop103`, `hadoop104`）转发访问请求，达到`access.log`中多个不同`IP`访问的效果。使用`fake_useragent`库实现对访问请求信息的随机生成，将`header`伪装成多个不同来源，如不同的浏览器、操作系统等。

### 为代理服务器配置squid转发

- 在代理服务器上以root用户身份执行安装`squid`：

```bash
yum install squid # hadoop102-104服务器使用的是CentOS系统
```

- 修改 Squid 配置文件`/etc/squid/squid.conf`，进行相应更改并完成配置：

```bash
http_port 3128 # 默认监听地址和端口
http_access allow all # 允许所有客户端连接
-------------------------------------------------------
systemctl restart squid # 保存配置文件并重新启动squid服务
```

- 使用集群分发脚本`xsync`同步所有`hadoop`服务器的代理配置信息：

```bash
xsync /etc/squid/squid.conf # 见[Hadoop3.x Basics](http://124.222.120.214/media/notion_files/070523/hadoop_basics_notes.html)
```

### 部署基于Nginx架构的网站

运行网站的服务器端采用基于Django的web架构，并通过nginx进行部署。有关该网站架构的技术细节，可以参照我另一篇笔记：[**`Django Basics`**](http://124.222.120.214/media/notion_files/070923/Django%20Basics%20668d2388c67b47869a192459163ec675.html)

关于该网站的nginx配置信息，可以参照这份配置时留存的操作备份：[`deploy_nginx_on_server`](http://124.222.120.214/media/notion_files/070923/deploy_nginx_on_server.txt)

- 使用`uwsgi`运行`Django`工程，并启动`nginx`服务使之在内网上线：

```bash
nohup uwsgi --ini uwsgi.ini &
service nginx start
```

- 在Windows主机访问`nginx`网站`homepage.html`页面，页面返回正常。
- 检查`access.log`中是否正确生成了日志：

```bash
# 相比原文件，增加了新访问时生成的3条日志，分别获取了主页的html,css,和js文件：
192.168.10.1 - - [09/Jul/2023:20:51:23 +0800] "GET /homepage/ HTTP/1.1" 200 5266 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67"
192.168.10.1 - - [09/Jul/2023:20:51:23 +0800] "GET /static/js/scripts.js HTTP/1.1" 404 1035 "http://192.168.10.128/homepage/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67"
192.168.10.1 - - [09/Jul/2023:20:51:23 +0800] "GET /static/css/styles.css HTTP/1.1" 404 1029 "http://192.168.10.128/homepage/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67"
```

### 通过代理转发、header伪装、自动化脚本生成大量日志数据

- 如程序设计概述中所述，使用`requests`库实现批量访问：

```python
import requests
from fake_useragent import UserAgent

def send_proxy_requests():
    proxy_list = ['hadoop102:3128', 'hadoop103:3128', 'hadoop104:3128']  # 代理服务器列表
    nginx_url = 'http://192.168.10.128/homepage/'  # Nginx的URL

    for proxy in proxy_list:
        proxies = {
            'http': 'http://' + proxy,
            'https': 'https://' + proxy
        }

        user_agent = UserAgent().random
        headers = {'User-Agent': user_agent}

        try:
            response = requests.get(nginx_url, proxies=proxies, headers=headers)
            print('IP {} 访问结果: {}'.format(proxy, response.status_code))
        except requests.exceptions.RequestException as e:
            print('IP {} 访问异常: {}'.format(proxy, str(e)))

def send_local_request():
    nginx_url = 'http://192.168.10.128/homepage/'
    try:
        response = requests.get(nginx_url)
        print('IP {} 访问结果: {}'.format("localhost:80", response.status_code))
    except requests.exceptions.RequestException as e:
        print('IP {} 访问异常: {}'.format("localhost:80", str(e)))

# 测试：生成400条数据：
for request_index in range(100):
    send_proxy_requests()
    send_local_request()
59-458
```

- 查看access.log，成功生成相应的日志文件。该日志文件的下载链接：[`access.log`](http://124.222.120.214/download/access_log.txt)
- 其中第59行~458行为运行上述代码生成的日志，前58行为此前其他测试生成。

```python
# 部分日志一览（240~249）
192.168.10.103 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Linux i686 ; en) Opera 9.70"
192.168.10.104 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.10  [en]"
192.168.10.1 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 5266 "-" "python-requests/2.31.0"
192.168.10.102 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_2; pt-br) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13"
192.168.10.103 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; nl-nl) AppleWebKit/418.8 (KHTML, like Gecko) Safari/419.3"
192.168.10.104 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.59 Safari/525.19"
192.168.10.1 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 5266 "-" "python-requests/2.31.0"
192.168.10.102 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.8.1.12) Gecko/20080208 Fedora/2.0.0.12-1.fc8 Firefox/2.0.0.12"
192.168.10.103 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14931"
192.168.10.104 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; en) Opera 11.00"
```

## Reference

- 在操作过程中采用了的ChatGPT提供的建议的对话链接：

[ChatGPT](https://chat.openai.com/share/16f97992-a96a-4c43-9970-7c963f9e1be0)

# Hadoop3.x Basics

Created: September 12, 2024 1:48 PM
Labels & Language: CentOS, Hadoop, Java
Source: https://www.bilibili.com/video/BV1Qp4y1n7EN/

## 引言

Hadoop是大数据技术中重要的框架之一。在Hadoop的基础上，能够更容易地开发和运行其他处理大规模数据的框架。作为学习笔记，本文包括Hadoop的理论和在CentOS上的应用实践，包括配置和基本命令等。

## Hadoop3.x 学习笔记 - 基础篇

### 使用VMware虚拟机进行CentOS的配置和安装

1. 在本机中安装CentOS 7镜像的虚拟机，命名为hadoop100
2. 在虚拟网络编辑器中，设置NAT网络，VMnet8，子网IP设置为10端口
3. 在网络适配器控制面板中设置该适配器默认网关为192.168.10.2
4. 将Hadoop100设置为静态IP地址，以确保本机能够找到该服务器，并添加其他相关配置。修改主机名称，配置主机名称映射等。

```bash
[root@hadoop100 chriswang]# vim /etc/sysconfig/network-scripts/ifcfg-ens33
--------------------------------------------------------------------------
# BOOTPROTO="dhcp"
# 修改为：
BOOTPROTO="static"
# 添加IP地址、网关、域名解析器
IPADDR=192.168.10.100
GATEWAY=192.168.10.2
DNS1=192.168.10.2
--------------------------------------------------------------------------
# 修改主机名称为hadoop100
[root@hadoop100 chriswang]# vim /etc/hostname
# 修改主机名称映射
[root@hadoop100 chriswang]# vim /etc/hosts
--------------------------------------------------------------------------
# 添加映射给至多8台服务器
......
192.168.10.100 hadoop100
192.168.10.101 hadoop101
......
192.168.10.108 hadoop108
--------------------------------------------------------------------------
# 重启以更新配置
[root@hadoop100 chriswang]# reboot
```

1. 使用本机PowerShell通过ssh协议模拟远程连接，成功。

```powershell
PS C:\Users\10131> ssh chriswang@192.168.10.100
chriswang@192.168.10.100's password:
Last login: Tue Jul  4 19:05:39 2023
```

1. 配置Windows地址映像，地址为`C:\Windows\System32\drivers\etc\hosts`
2. CentOS环境配置 - 基本工具&环境

```bash
[chriswang@hadoop100 ~]$ sudo yum install -y epel-release
[chriswang@hadoop100 ~]$ sudo systemctl stop firewalld
[chriswang@hadoop100 ~]$ sudo systemctl disable firewalld.service
Removed symlink /etc/systemd/system/multi-user.target.wants/firewalld.service.
Removed symlink /etc/systemd/system/dbus-org.fedoraproject.FirewallD1.service.
# 清理预装java工具
[root@hadoop100 chriswang]# rpm -qa | grep -i java | xargs -n1 rpm -e --nodeps
```

### 克隆多台虚拟机以模拟分布式集群

- 使用VMware内置克隆工具，选择完全克隆即可
- 对克隆后的服务器进行配置修改，即`(100 —> 102, 103, 104)`

### 安装并配置Java JDK和Hadoop

- 安装Java JDK后，配置全局声明：

```java
#JAVA_HOME
export JAVA_HOME=/home/chriswang/Applications/jdk1.8.0_212
export PATH=$PATH:$JAVA_HOME/bin
```

- 安装Hadoop后，添加声明：

```java
#HADOOP_HOME
export HADOOP_HOME=/home/chriswang/Applications/hadoop-3.1.3
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin
```

- 随后使用`source /etc/profile`即可开启该位置注册过的所有服务

### 完全分布式的运行模式

1. 编写集群分发脚本`xsync`
- 使用`scp`命令拷贝工具和环境至其他服务器

```bash
# 在hadoop102上执行：
scp -r /home/chriswang/Applications/jdk1.8.0_212/ root@hadoop104:/home/chriswang/Applications
scp -r /home/chriswang/Applications/jdk1.8.0_212/ root@hadoop103:/home/chriswang/Applications
```

- 或使用以`rsync`为基础的`xsync`集群分发脚本

a. 在`/home/chriswang/bin`下创建`bash`命令文件`xsync`：

```bash
#!/bin/bash
#1. 判断参数个数
if [ $# -lt 1 ]
then
 echo Not Enough Arguement!
 exit;
fi
#2. 遍历集群所有机器
for host in hadoop102 hadoop103 hadoop104
do
 echo ==================== $host ====================
 #3. 遍历所有目录，挨个发送
 for file in $@
 do
 #4. 判断文件是否存在
 if [ -e $file ]
 then
 #5. 获取父目录
 pdir=$(cd -P $(dirname $file); pwd)
 #6. 获取当前文件的名称
 fname=$(basename $file)
 ssh $host "mkdir -p $pdir"
 rsync -av $pdir/$fname $host:$pdir
 else
 echo $file does not exists!
 fi
 done
done
```

b. 修改`xsync`脚本权限，并将脚本复制到`/bin`中，以便全局调用

```bash
chmod +x xsync
sudo cp xsync /bin/
```

c. 使用`xsync`脚本将`kafka`部署至其他服务器

```bash
xsync ../Applications/kafka/
```

## Other References

- 中文教程 - 尚硅谷Bilibili
    
    [尚硅谷大数据Hadoop教程，hadoop3.x搭建到集群调优，百万播放_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1Qp4y1n7EN/)
    
- 官方文档 - Apache Hadoop 3.3.6
    
    [Apache Hadoop 3.3.6 – Hadoop: Setting up a Single Node Cluster.](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html)
    
- 建议学习路线图 - 尚硅谷Bilibili
    
    [2023最新大数据学习路线图](https://www.bilibili.com/read/cv5213600)

# Kafka3.x Basics

Created: September 12, 2024 1:48 PM
Labels & Language: CentOS, Kafka
Source: https://www.bilibili.com/video/BV1vr4y1677k/

## 引言

Kafka是一个开源的分布式流处理平台，最初由LinkedIn开发并于2011年开源。它被设计用于处理高容量的实时数据流，包括日志、事件流和其他实时数据。Kafka通常被用作一种可靠的消息系统，采用发布-订阅模式，其中数据被组织成所谓的"topic"，并且可以被多个消费者订阅。生产者可以将消息发布到特定的topic中，而消费者则可以从这些topic中读取消息并进行处理。

## Kafka3.x 基础篇

### 安装和配置kafka于CentOS

1. 修改`config`文件`server.properties`

```bash
# A comma separated list of directories under which to store log files
# log.dirs=/tmp/kafka-logs 修改为：
log.dirs=/home/chriswang/Applications/kafka/data
# zookeeper.connect = localhost:2181 修改为：
zookeeper.connect=hadoop102:2181,hadoop103:2181,hadoop104:2181/kafka
# hadoop服务器102-104配置信息见[Hadoop3.x Basics](http://124.222.120.214/media/notion_files/070523/hadoop_basics_notes.html)
```

1. 修改hadoop服务器的`broker.id`，即分别在`hadoop103`和`hadoop104`上修改配置文件中的`/home/chriswang/Applications/kafka/config/server.properties`中的 `broker.id=1`， `broker.id=2`
2. 基础zookeeper操作

```java
bin/zkServer.sh start 开启服务端
bin/zkCli.sh 开启客户端
quit 退出界面
```

## Other References

[【尚硅谷】Kafka3.x教程（从入门到调优，深入全面）_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1vr4y1677k/)

# Flume & Kafka Stream

Created: September 12, 2024 1:48 PM
Labels & Language: Java, Kafka, flume
Source: https://flume.apache.org/releases/content/1.11.0/FlumeUserGuide.html

## 引言

将`nginx`日志通过`Flume`采集到Kafka。在这个过程中，`nginx`作为`source`，`kafka`作为`sink`的对象。`Flume`是一个强大的日志采集工具，`kafka`则可以有效地对服务器进行分布式管理。

## Flume & Kafka 日志文件流

### Https Requests → Nginx → Flume → Kafka

1. 测试Flume功能 - 使用`Linux nc`命令测试`Flume`是否配置正确

```
# Name the components on this agenta1.sources= r1
a1.sinks= k1
a1.channels= c1

# Describe/configure the sourcea1.sources.r1.type= netcat
a1.sources.r1.bind= localhost
a1.sources.r1.port= 44444

# Describe the sinka1.sinks.k1.type= logger

# Use a channel which buffers events in memorya1.channels.c1.type= memory
a1.channels.c1.capacity= 1000
a1.channels.c1.transactionCapacity= 100

# Bind the source and sink to the channela1.sources.r1.channels= c1
a1.sinks.k1.channel= c1

# Flume启动
bin/flume-ng agent --conf conf --conf-file example.conf --name a1
bin/flume-ng agent -n a1 -c conf/ -f job/net-flume-logger.conf -Dflume.root.logger=INFO,console
```

使用nc命令监听指定接口，收到返回，测试成功：

```java
2023-08-02 19:37:33,287 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.LoggerSink.process(LoggerSink.java:95)] Event: { headers:{} body: 31 39 32 2E 31 36 38 2E 31 30 2E 31 20 2D 20 2D 192.168.10.1 - - }
2023-08-02 19:39:07,300 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.LoggerSink.process(LoggerSink.java:95)] Event: { headers:{} body: 31 39 32 2E 31 36 38 2E 31 30 2E 31 20 2D 20 2D 192.168.10.1 - - }
2023-08-02 19:39:29,518 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.LoggerSink.process(LoggerSink.java:95)] Event: { headers:{} body: 31 39 32 2E 31 36 38 2E 31 30 2E 31 20 2D 20 2D 192.168.10.1 - - }
```

1. 编写`Flume`配置文件实现将`nginx`日志作为源，`sink`进入`kafka`

```java
pro.sources = s1
pro.channels = c1
pro.sinks = k1

pro.sources.s1.type = exec
pro.sources.s1.command = tail -F /var/log/nginx/access.log

pro.channels.c1.type = memory
pro.channels.c1.capacity = 1000
pro.channels.c1.transactionCapacity = 100

pro.sinks.k1.type = org.apache.flume.sink.kafka.KafkaSink
pro.sinks.k1.kafka.topic = moercredit_log_test
pro.sinks.k1.kafka.bootstrap.servers = localhost:9092
pro.sinks.k1.kafka.flumeBatchSize = 20
pro.sinks.k1.kafka.producer.acks = 1
pro.sinks.k1.kafka.producer.linger.ms = 1
pro.sinks.k1.kafka.producer.compression.type = snappy

pro.sources.s1.channels = c1
pro.sinks.k1.channel = c1

---------------------------------------------------------
bin/flume-ng agent -n pro -c conf/ -f conf/flume2kafka.conf -Dflume.root.logger=INFO,console
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic moercredit_log_test --from-beginning
```

1. 先后分别打开`zookeeper`，`kafka`，`flume`服务。并运行`http`自动访问`python`脚本
2. `kafka`信息接受窗口收到返回，成功：

```java
# kafka获得日志流数据形如：
192.168.10.102 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/75.0"
192.168.10.103 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 3.0)"
192.168.10.104 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Opera/9.63 (X11; Linux x86_64; U; ru) Presto/2.1.1"
192.168.10.1 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 2650 "-" "python-requests/2.31.0"
192.168.10.102 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Mozilla/4.0 (compatible; MSIE 5.0; Linux 2.4.19-4GB i686) Opera 6.11  [en]"
192.168.10.103 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.343.0 Safari/533.2"
192.168.10.104 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008110715 ASPLinux/3.0.2-3.0.120asp Firefox/3.0.2"
192.168.10.1 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 2650 "-" "python-requests/2.31.0"
[^C mannual stop] Processed a total of 234 messages
```

1. 查看`kafka data`文件，发现部分乱码，暂无解决。

## Other sources & Reference

[Flume 1.11.0 User Guide — Apache Flume](https://flume.apache.org/releases/content/1.11.0/FlumeUserGuide.html)

# Flink & Elasticsearch Stream

Created: September 12, 2024 1:48 PM

## Description

完成nginx日志数据处理数据流的最后一步，导入Flink进行流式计算，以及使用ES进行数据可视化。

## Flink & Elasticsearch Stream

### 安装Elasticsearch和Elasticsearch-head

1. 安装`es`图形化`chrome`插件`es-head`
2. 配置`es`并排除故障

```java
# 修改sysctl.conf解决虚拟内存溢出问题
vm.max_map_count=655360
sysctl -p # 完成修改
----------------------------------
./elasticsearch # 启动es服务
```

1. `es-head`进入`localhost:9200`查看，返回`green`，连接成功。

## Other sources & Reference

[flink 消费 kafka数据，将结果写入到elasticsearch中_flink读取kafka数据 写入es_慕雨潇潇的博客-CSDN博客](https://blog.csdn.net/dlhszn1mfy/article/details/89675942)