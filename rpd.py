import sys
import kubernetes as k8s
import numpy as np

from utils import convert, get_k8s_object, monitor


def get_node_rpd(k8s_node, t0=None, have_t0=False):
    nodes = convert.convert_all_k8s_nodes_to_my_nodes()
    node = nodes[k8s_node.metadata.name]
    http_cpu_occupy = (1 - monitor.http_get_node_free_rate_monitor("cpu")[node.name]) * node.capacity_cpu
    http_mem_occupy = (1 - monitor.http_get_node_free_rate_monitor("mem")[node.name]) * node.capacity_memory
    # print(node.name)
    if have_t0:
        # print("have_t0")
        occupy_cpu = http_cpu_occupy + t0.cpu_request
        occupy_mem = http_mem_occupy + t0.memory_request
    else:
        # print("have_no_t0")
        occupy_cpu = http_cpu_occupy
        occupy_mem = http_mem_occupy
    # print(f"node:: {k8s_node.metadata.name} occupy_cpu:: {occupy_cpu}")
    # print(f"node:: {k8s_node.metadata.name} occupy_mem:: {occupy_mem}")
    r_cpu = occupy_cpu / node.capacity_cpu
    r_mem = occupy_mem / node.capacity_memory
    r_avg = (r_mem + r_cpu) / 2
    rpd = abs(r_cpu - r_mem) / r_avg
    return rpd


def record(name):
    k8s.config.load_kube_config(config_file=".kube/config")
    # 记录结果
    nodes = get_k8s_object.k8s_nodes_available(only_name=False, is_edge=True)
    rpd_list = []
    node_cpu_use = dict()
    node_mem_use = dict()
    for i in nodes:
        rpd_list.append(get_node_rpd(i))
    variance = np.var(rpd_list)
    nodes_cpu = monitor.http_get_node_free_rate_monitor("cpu")
    nodes_mem = monitor.http_get_node_free_rate_monitor("mem")
    for node_name, val in nodes_cpu.items():
        node_cpu_use[node_name] = 1 - val
        node_mem_use[node_name] = 1 - nodes_mem[node_name]
    filename = 'default_output2.txt'
    with open(filename, "a") as f:
        old_stdout = sys.stdout
        sys.stdout = f
        print(f"节点cpu利用率:: {node_cpu_use} 内存利用率:: {node_mem_use}")
        print("---->各节点相似度相对差异<----")
        print(f"rpd_list:: {rpd_list}")
        if name is not None:
            print(f"pod::{name} 部署后集群相似度相对差异方差:: {variance}")
        else:
            print(f"集群相似度相对差异方差:: {variance}")
        print("---->节点资源利用率<----")
        print("------------------------------------")
        sys.stdout = old_stdout  # 恢复原来的stdout


if __name__ == '__main__':
    record(name=None)
