from config import config as custom_config
from utils import get_k8s_object
import requests


# 使用量
def http_get_node_usage_monitor(req):
    url = ''
    if req == "mem":
        url = custom_config.NodeMemURL
    elif req == "cpu":
        url = custom_config.NodeCpuURL
    res = requests.get(url)
    res_json = res.json()
    node_monitor = dict()
    node = []
    if res_json["status"] == 'success':
        result = res_json["data"]["result"]
        for v in result:
            node.append(v)
            node_name = get_k8s_object.get_node_name_by_ip(v["metric"]["instance"].replace(":9100", ""))
            node_val = float(v["value"][1])
            node_monitor[node_name] = node_val
    return node_monitor


def http_get_node_disk_rate_monitor():
    node_disk_rate = dict()
    for i in custom_config.EDGE_NODES_IPs.values():
        url = custom_config.NodeDiskURL.replace("{NODE_IP}", f"{i}:9100")
        node_name = get_k8s_object.get_node_name_by_ip(i)
        res = requests.get(url)
        res_json = res.json()
        if res_json["status"] == 'success':
            result = res_json["data"]["result"]
            val_temp = float(result[0]['value'][1])
            node_disk_rate[node_name] = val_temp
    return node_disk_rate


# 空闲率
def http_get_node_free_rate_monitor(req):
    url = ''
    if req == "mem":
        url = custom_config.NodeMemFreeURL
    elif req == "cpu":
        url = custom_config.NodeCpuFreeURL
    res = requests.get(url)
    res_json = res.json()
    node_monitor = dict()
    node = []
    if res_json["status"] == 'success':
        result = res_json["data"]["result"]
        for v in result:
            node.append(v)
            node_name = get_k8s_object.get_node_name_by_ip(v["metric"]["instance"].replace(":9100", ""))
            node_val = float(v["value"][1])
            node_monitor[node_name] = node_val
    return node_monitor


# 传pod名，获取cpu使用量或内存使用量
def http_get_pod_monitor(req, pod_name):
    val = 0
    if req == "mem":
        url = custom_config.PodMemURL.replace("{POD_NAME}", pod_name)
        res = requests.get(url)
        res_json = res.json()
        if res_json["status"] == 'success':
            result = res_json["data"]["result"]
            for v in result:
                val_temp = float(v['value'][1])
                val = max(val_temp, val)
    elif req == "cpu":
        url = custom_config.PodCpuURL.replace("{POD_NAME}", pod_name)
        res = requests.get(url)
        res_json = res.json()
        if res_json["status"] == 'success':
            result = res_json["data"]["result"]
            if result is not None:
                val_temp = float(result[0]['value'][1])
                val = max(val_temp, val)
    return val


if __name__ == '__main__':
    print(http_get_node_disk_rate_monitor())
