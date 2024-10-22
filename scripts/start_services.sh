#!/bin/bash

# Start Zookeeper
echo "Starting Zookeeper..."
zookeeper-server-start.sh kafka/zookeeper.properties &

# Start Kafka
echo "Starting Kafka..."
kafka-server-start.sh kafka/server.properties &

# Start Flume
echo "Starting Flume..."
flume-ng agent --conf flume/ --conf-file flume/flume.conf --name a1 &

# Start Nginx
echo "Starting Nginx..."
sudo nginx -c $(pwd)/nginx/nginx.conf

# Start Elasticsearch
echo "Starting Elasticsearch..."
sysctl -w vm.max_map_count=655360
elasticsearch &
