# General Methodology of Handling the Integration of Big Dataflow on a Linux Server

# 1. Nginx Access.log Generator

Created: September 12, 2024, 1:48 PM  
Labels & Language: Python, HTTP, Nginx  

## Introduction

Nginx is a popular open-source web server and reverse proxy server technology. It is designed to handle high-traffic websites and serve web content quickly and efficiently. Nginx can also be used as a load balancer, HTTP cache, proxy server for email protocols (IMAP, POP3, and SMTP), and more. The technical details in this note aim to simulate multiple IP logins to access Nginx's `index.html` page and generate access logs at a scale of up to tens of millions per day. These log files will serve as a basis for subsequent analysis.

## Generating Access Logs with Nginx

### Program Design Overview

Considering the nature and cost of the project, we will deploy a Django project with an Nginx architecture on a local virtual machine, simulating a public-facing website (while operating within the local network). The virtual machine server uses the Ubuntu Linux operating system. The local host running Windows serves as the entity making access requests. Using an automated script written with the `python requests` library, we will perform large-scale access operations (up to tens of millions). In this script, besides local access, to simulate multiple virtual `IP` addresses, we use Squid-based proxy technology, where three other servers (named `hadoop102`, `hadoop103`, and `hadoop104`) configured with Squid proxies forward the requests to create the effect of multiple different IP addresses accessing the `access.log`. The `fake_useragent` library is used to randomly generate request information, disguising the `header` as coming from different browsers, operating systems, etc.

### Configuring Squid Proxies on Servers

- Install Squid on the proxy server as the root user:

```bash
yum install squid # The hadoop102-104 servers are running CentOS
```

- Modify the Squid configuration file `/etc/squid/squid.conf` accordingly and complete the setup:

```bash
http_port 3128 # Default listening address and port
http_access allow all # Allow connections from all clients
-------------------------------------------------------
systemctl restart squid # Save the configuration file and restart the Squid service
```

- Synchronize the proxy configuration across all `hadoop` servers using the cluster distribution script `xsync`:

```bash
xsync /etc/squid/squid.conf # See [Hadoop3.x Basics](http://124.222.120.214/media/notion_files/070523/hadoop_basics_notes.html)
```

### Deploying the Website with Nginx Architecture

The server running the website uses a Django-based web architecture, deployed through Nginx. For more technical details on this architecture, refer to another note of mine: [**`Django Basics`**](http://124.222.120.214/media/notion_files/070923/Django%20Basics%20668d2388c67b47869a192459163ec675.html).

For the Nginx configuration, refer to this backup: [`deploy_nginx_on_server`](http://124.222.120.214/media/notion_files/070923/deploy_nginx_on_server.txt)

- Run the `Django` project using `uwsgi` and start the `nginx` service to bring it online within the local network:

```bash
nohup uwsgi --ini uwsgi.ini &
service nginx start
```

- Access the `homepage.html` page from the Nginx website using the Windows host, and confirm the page returns successfully.
- Check whether the `access.log` has logged the access correctly:

```bash
# The original log file now contains 3 additional entries from the recent access:
192.168.10.1 - - [09/Jul/2023:20:51:23 +0800] "GET /homepage/ HTTP/1.1" 200 5266 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.1823.67"
192.168.10.1 - - [09/Jul/2023:20:51:23 +0800] "GET /static/js/scripts.js HTTP/1.1" 404 1035 "http://192.168.10.128/homepage/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.1823.67"
192.168.10.1 - - [09/Jul/2023:20:51:23 +0800] "GET /static/css/styles.css HTTP/1.1" 404 1029 "http://192.168.10.128/homepage/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.1823.67"
```

### Generating Large Volumes of Log Data with Proxy Forwarding, Header Spoofing, and Automated Scripts

- As described in the program design overview, batch access is implemented using the `requests` library:

```python
import requests
from fake_useragent import UserAgent

def send_proxy_requests():
    proxy_list = ['hadoop102:3128', 'hadoop103:3128', 'hadoop104:3128']  # Proxy server list
    nginx_url = 'http://192.168.10.128/homepage/'  # Nginx URL

    for proxy in proxy_list:
        proxies = {
            'http': 'http://' + proxy,
            'https': 'https://' + proxy
        }

        user_agent = UserAgent().random
        headers = {'User-Agent': user_agent}

        try:
            response = requests.get(nginx_url, proxies=proxies, headers=headers)
            print(f'IP {proxy} access result: {response.status_code}')
        except requests.exceptions.RequestException as e:
            print(f'IP {proxy} access error: {str(e)}')

def send_local_request():
    nginx_url = 'http://192.168.10.128/homepage/'
    try:
        response = requests.get(nginx_url)
        print(f'IP localhost:80 access result: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'IP localhost:80 access error: {str(e)}')

# Test: generate 400 log entries
for request_index in range(100):
    send_proxy_requests()
    send_local_request()
```

- Check the access.log and confirm that the log file has been successfully generated. The download link for the log file: [`access.log`](http://124.222.120.214/download/access_log.txt).  
- Lines 59–458 were generated by running the script above, while lines 1–58 were generated from earlier tests.

```python
# Sample logs (240–249)
192.168.10.103 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Opera 9.70"
192.168.10.104 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Opera 7.10 [en]"
192.168.10.1 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 5266 "-" "python-requests/2.31.0"
192.168.10.102 - - [09/Jul/2023:21:20:48 +0800] "GET /homepage/ HTTP/1.1" 200 21552 "-" "Safari/3.1"
```

## Reference

- Suggestions provided by ChatGPT during the process:  
  [ChatGPT](https://chat.openai.com/share/16f97992-a96a-4c43-9970-7c963f9e1be0)

# 2. Hadoop3.x Workflow

Created: September 12, 2024, 1:48 PM  
Labels & Language: CentOS, Hadoop, Java  
Source: https://www.bilibili.com/video/BV1Qp4y1n7EN/

## Introduction

Hadoop is one of the key frameworks in big data technology. It provides a foundation for developing and running other frameworks that handle large-scale data. As study notes, this document covers both theoretical and practical applications of Hadoop on CentOS, including configurations and basic commands.

## Hadoop3.x Learning Notes - Basics

### Configuring and Installing CentOS Using VMware Virtual Machine

1. Install a CentOS 7 virtual machine on the local host, named hadoop100.
2. In the virtual network editor, set up a NAT network (VMnet8) and configure the subnet IP to use port 10.
3. In the network adapter control panel, set the adapter's default gateway to 192.168.10.2.
4. Assign a static IP address to hadoop100 to ensure the local machine can find the server and add other necessary configurations. Modify the hostname and set up hostname mapping.

```bash
[root@hadoop100 chriswang]# vim /etc/sysconfig/network-scripts/ifcfg-ens33
--------------------------------------------------------------------------
# BOOTPROTO="dhcp"
# Change to:
BOOTPROTO="static"
# Add IP address, gateway, and DNS resolver
IPADDR=192.168.10.100
GATEWAY=192.168.10.2
DNS1=192.168.10.2
--------------------------------------------------------------------------
# Change hostname to hadoop100
[root@hadoop100 chriswang]# vim /etc/hostname
# Modify the hostname mapping
[root@hadoop100 chriswang]# vim /etc/hosts
--------------------------------------------------------------------------
# Add mappings for up to 8 servers
......
192.168.10.100 hadoop100
192.168.10.101 hadoop101
......
192.168.10.108 hadoop108
--------------------------------------------------------------------------
# Reboot to apply the configuration
[root@hadoop100 chriswang]# reboot
```

1. Successfully simulated a remote connection using the local machine's PowerShell via SSH.

```powershell
PS C:\Users\10131> ssh chriswang@192.168.10.100
chriswang@192.168.10.100's password:
Last login: Tue Jul  4 19:05:39 2023
```

1. Configure the Windows host mapping file located at `C:\Windows\System32\drivers\etc\hosts`.

2. Configure the CentOS environment - install essential tools and configure the system.

```bash
[chriswang@hadoop100 ~]$ sudo yum install -y epel-release
[chriswang@hadoop100 ~]$ sudo systemctl stop firewalld
[chriswang@hadoop100 ~]$ sudo systemctl disable firewalld.service
Removed symlink /etc/systemd/system/multi-user.target.wants/firewalld.service.
Removed symlink /etc/systemd/system/dbus-org.fedoraproject.FirewallD1.service.
# Remove pre-installed Java tools
[root@hadoop100 chriswang]# rpm -qa | grep -i java | xargs -n1 rpm -e --nodeps
```

### Cloning Multiple Virtual Machines to Simulate a Distributed Cluster

- Use VMware's built-in clone tool, selecting "Full Clone" for each virtual machine.
- Modify the configuration of each cloned server to reflect changes (i.e., update IPs from hadoop100 to hadoop102, hadoop103, etc.).

### Installing and Configuring Java JDK and Hadoop

1. Install Java JDK and configure the global environment variables:

```bash
# JAVA_HOME
export JAVA_HOME=/home/chriswang/Applications/jdk1.8.0_212
export PATH=$PATH:$JAVA_HOME/bin
```

2. Install Hadoop and add its environment variables:

```bash
# HADOOP_HOME
export HADOOP_HOME=/home/chriswang/Applications/hadoop-3.1.3
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin
```

- Afterward, use `source /etc/profile` to activate the services registered in the profile.

### Fully Distributed Mode

1. Write a cluster distribution script called `xsync` to distribute files across the cluster.
- Use the `scp` command to copy tools and environments to other servers.

```bash
# On hadoop102:
scp -r /home/chriswang/Applications/jdk1.8.0_212/ root@hadoop104:/home/chriswang/Applications
scp -r /home/chriswang/Applications/jdk1.8.0_212/ root@hadoop103:/home/chriswang/Applications
```

- Alternatively, use the `xsync` script, which is based on `rsync`, to synchronize files across the cluster.

a. Create the `xsync` bash script in `/home/chriswang/bin`:

```bash
#!/bin/bash
# 1. Check the number of arguments
if [ $# -lt 1 ]
then
 echo "Not Enough Arguments!"
 exit;
fi
# 2. Iterate through all cluster machines
for host in hadoop102 hadoop103 hadoop104
do
 echo "==================== $host ===================="
 # 3. Iterate through all directories, sending each one
 for file in $@
 do
 # 4. Check if the file exists
 if [ -e $file ]
 then
 # 5. Get the parent directory
 pdir=$(cd -P $(dirname $file); pwd)
 # 6. Get the current file's name
 fname=$(basename $file)
 ssh $host "mkdir -p $pdir"
 rsync -av $pdir/$fname $host:$pdir
 else
 echo "$file does not exist!"
 fi
 done
done
```

b. Change the permissions of the `xsync` script and copy it to `/bin/` to allow global access.

```bash
chmod +x xsync
sudo cp xsync /bin/
```

c. Use the `xsync` script to deploy `kafka` to other servers.

```bash
xsync ../Applications/kafka/
```

## Other References

- Chinese tutorial:  
  [尚硅谷 Hadoop3.x Video Tutorial](https://www.bilibili.com/video/BV1Qp4y1n7EN/)
  
- Official documentation:  
  [Apache Hadoop 3.3.6 – Setting up a Single Node Cluster](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html)

- Recommended Learning Roadmap:  
  [2023 Big Data Learning Roadmap](https://www.bilibili.com/read/cv5213600)

# 3. Kafka3.x Workflow

Created: September 12, 2024, 1:48 PM  
Labels & Language: CentOS, Kafka  
Source: https://www.bilibili.com/video/BV1vr4y1677k/

## Introduction

Kafka is an open-source distributed stream processing platform, initially developed by LinkedIn and open-sourced in 2011. It is designed to handle high volumes of real-time data streams, such as logs, event streams, and other real-time data. Kafka is often used as a reliable messaging system, adopting a publish-subscribe model where data is organized into "topics" that can be subscribed to by multiple consumers. Producers publish messages to specific topics, while consumers read messages from these topics and process them.

## Kafka3.x Basics

### Installing and Configuring Kafka on CentOS

1. Modify the `server.properties` configuration file:

```bash
# A comma-separated list of directories for storing log files
# log.dirs=/tmp/kafka-logs Change to:
log.dirs=/home/chriswang/Applications/kafka/data
# zookeeper.connect = localhost:2181 Change to:
zookeeper.connect=hadoop102:2181,hadoop103:2181,hadoop104:2181/kafka
# Configuration details for the hadoop servers 102-104 can be found in [Hadoop3.x Basics](http://124.222.120.214/media/notion_files/070523/hadoop_basics_notes.html)
```

2. Modify the `broker.id` on each hadoop server. For `hadoop103` and `hadoop104`, update the `broker.id` in `/home/chriswang/Applications/kafka/config/server.properties`:

- On `hadoop103`:  
  `broker.id=1`  
- On `hadoop104`:  
  `broker.id=2`

3. Basic Zookeeper operations:

```bash
bin/zkServer.sh start # Start the Zookeeper server
bin/zkCli.sh # Start the Zookeeper client
quit # Exit the client interface
```

### Running Kafka in a Fully Distributed Mode

After configuring Zookeeper and Kafka, Kafka is now set up to handle distributed stream processing across multiple servers.

1. Start the Kafka server on each node.
2. Run the Zookeeper service to manage the distributed coordination of Kafka brokers.

## Other References

- Kafka Tutorial Video:  
  [【尚硅谷】Kafka3.x Tutorial (Comprehensive and In-depth)](https://www.bilibili.com/video/BV1vr4y1677k/)

---

# 4. Flume & Kafka Stream

Created: September 12, 2024, 1:48 PM  
Labels & Language: Java, Kafka, Flume  
Source: https://flume.apache.org/releases/content/1.11.0/FlumeUserGuide.html

## Introduction

In this setup, Nginx logs are collected via Flume and ingested into Kafka. In this pipeline, Nginx acts as the "source" while Kafka serves as the "sink". Flume is a powerful tool for log collection, and Kafka can efficiently manage distributed servers.

## Flume & Kafka Log File Streaming

### HTTP Requests → Nginx → Flume → Kafka

1. Test Flume's functionality by using the `nc` (netcat) command on Linux to ensure Flume is correctly configured.

```bash
# Define the components on this agent
a1.sources= r1
a1.sinks= k1
a1.channels= c1

# Configure the source
a1.sources.r1.type= netcat
a1.sources.r1.bind= localhost
a1.sources.r1.port= 44444

# Configure the sink
a1.sinks.k1.type= logger

# Set up a memory-based channel for buffering events
a1.channels.c1.type= memory
a1.channels.c1.capacity= 1000
a1.channels.c1.transactionCapacity= 100

# Bind the source and sink to the channel
a1.sources.r1.channels= c1
a1.sinks.k1.channel= c1

# Start Flume
bin/flume-ng agent --conf conf --conf-file example.conf --name a1
bin/flume-ng agent -n a1 -c conf/ -f job/net-flume-logger.conf -Dflume.root.logger=INFO,console
```

Using the `nc` command to listen on the specified interface, the response indicates that the test is successful:

```bash
2023-08-02 19:37:33,287 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.LoggerSink.process(LoggerSink.java:95)] Event: { headers:{} body: 192.168.10.1 - - }
2023-08-02 19:39:07,300 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.LoggerSink.process(LoggerSink.java:95)] Event: { headers:{} body: 192.168.10.1 - - }
2023-08-02 19:39:29,518 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.LoggerSink.process(LoggerSink.java:95)] Event: { headers:{} body: 192.168.10.1 - - }
```

2. Write a Flume configuration file to stream Nginx logs from Flume to Kafka:

```bash
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

# Start the Flume agent
bin/flume-ng agent -n pro -c conf/ -f conf/flume2kafka.conf -Dflume.root.logger=INFO,console
# Consume messages from Kafka
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic moercredit_log_test --from-beginning
```

3. Start the Zookeeper, Kafka, and Flume services sequentially, and run an HTTP auto-access Python script.
4. Kafka’s console will receive log stream data:

```bash
# Kafka received log stream data like:
192.168.10.102 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/75.0"
192.168.10.103 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 9825 "-" "Opera/9.63 (X11; Linux x86_64; U; ru) Presto/2.1.1"
192.168.10.1 - - [03/Aug/2023:02:06:58 +0800] "GET /index/ HTTP/1.1" 200 2650 "-" "python-requests/2.31.0"
```

5. Check the Kafka data files, and note that some data is garbled; the issue is unresolved for now.

## Other Sources & References

- [Flume 1.11.0 User Guide – Apache Flume](https://flume.apache.org/releases/content/1.11.0/FlumeUserGuide.html)

---

# 5. Flink & Elasticsearch Stream

Created: September 12, 2024, 1:48 PM

## Description

This is the final step in processing the Nginx log data stream: importing it into Flink for stream computation and using Elasticsearch (ES) for data visualization.

## Flink & Elasticsearch Stream

### Installing Elasticsearch and Elasticsearch-head

1. Install the Elasticsearch-head graphical plugin for Chrome.
2. Configure Elasticsearch and resolve any issues.

```bash
# Modify sysctl.conf to resolve virtual memory overflow issues
vm.max_map_count=655360
sysctl -p # Apply the changes
----------------------------------
./elasticsearch # Start the Elasticsearch service
```

3. Open Elasticsearch-head at `localhost:9200`, and the status returns `green`, indicating a successful connection.

## Other Sources & References

- [Consuming Kafka Data in Flink and Writing Results to Elasticsearch](https://blog.csdn.net/dlhszn1mfy/article/details/89675942)