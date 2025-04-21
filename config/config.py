NAMESPACE = "k8s"
SCHEDULER_NAME = 'custom-scheduler'
MASTER_NAME = 'K8smaster'
MASTER_IP = '192.168.11.90'
Prometheus_Port = 31000
CLOUD_NODES = ['k8smaster', 'k8snode1']
Edge_NODES = ['edge1', 'edge2', 'edge3', 'edge4']
CLOUD_NODES_IPs = {'k8smaster': '192.168.11.90', 'k8snode1': '192.168.11.95'}
EDGE_NODES_IPs = {'edge1': '192.168.11.91', 'edge2': '192.168.11.92', 'edge3': '192.168.11.93', 'edge4': '192.168.11.94'}
JOB = "edgenodes"
CADVISOR_JOB = "edge_cadvisor"
SPLITTING_CHAR = '-'
# POD_NAME = ''
# 过去2分钟的cpu空闲率
NodeCpuFreeURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=1 - (1 - avg by (instance) (rate(node_cpu_seconds_total{{mode="idle", job="{JOB}"}}[2m])))'
# 内存空闲率
NodeMemFreeURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=node_memory_MemAvailable_bytes{{job="{JOB}"}}%20/%20node_memory_MemTotal_bytes{{job="{JOB}"}}'
# # 过去2分钟的网络带宽(MB/s)
# NodeNetURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=(rate(node_network_receive_bytes_total{{job="{JOB}"}}[2m]) + rate(node_network_transmit_bytes_total{{job="{JOB}"}}[2m])) / 1024 / 1024'
# # 过去2分钟的磁盘IO(MB/s)
# NodeDiskIOURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=(rate(node_disk_read_bytes_total{{job="{JOB}"}}[2m]) + rate(node_disk_written_bytes_total{{job="{JOB}"}}[2m])) / 1024 / 1024'

# Node CPU 使用量查询URL（以2分钟平均值计算）（多少个毫核心）
NodeCpuURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=(1 - avg by (instance) (rate(node_cpu_seconds_total{{mode="idle", job="{JOB}"}}[2m])))*' \
             f'(count(count(node_cpu_seconds_total{{job="{JOB}"}}) by (cpu, instance)) by (instance))*1000'
# Node 内存使用量查询URL（字节数）
NodeMemURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=node_memory_MemTotal_bytes{{job="{JOB}"}} - node_memory_MemAvailable_bytes{{job="{JOB}"}}'

# Node 磁盘空间使用率查询URL
NodeDiskURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=1-sum(node_filesystem_avail_bytes{{instance="{{NODE_IP}}",fstype!="tmpfs", fstype!="squashfs"}})/sum(node_filesystem_size_bytes{{instance="{{NODE_IP}}",fstype!="tmpfs", fstype!="squashfs"}})'
# Pod CPU 使用量查询URL（以2分钟平均值计算）（多少个毫核心）
PodCpuURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=sum(rate(container_cpu_usage_seconds_total{{container_label_io_kubernetes_container_name != "POD"' \
            f',container_label_io_kubernetes_pod_namespace = "{NAMESPACE}", job = "{CADVISOR_JOB}", container_label_io_kubernetes_pod_name="{{POD_NAME}}"}}[2m]))*1000'

# Pod 内存使用量查询URL（字节数）
PodMemURL = f'http://{MASTER_IP}:{Prometheus_Port}/api/v1/query?query=container_memory_usage_bytes{{container_label_io_kubernetes_container_name != "POD", container_label_io_kubernetes_pod_namespace="{NAMESPACE}", ' \
            f'job="{CADVISOR_JOB}", container_label_io_kubernetes_pod_name="{{POD_NAME}}"}} '


pod_time = dict({"demo1": 780,
                 "demo2": 380,
                 "demo3": 141,
                 "demo4": 187,
                 "demo5": 389,
                 "demo6": 215,
                 "demo7": 159,
                 "demo8": 258})