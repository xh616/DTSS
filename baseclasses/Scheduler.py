import math
import sys

from kubernetes import client
from kubernetes.client import ApiException

from config import config as custom_config
from utils import convert, get_k8s_object, monitor
import datetime
import numpy as np
import time


class CustomScheduler:
    def __init__(self, scheduler_name=custom_config.SCHEDULER_NAME):
        # k8s v1 API 获取节点和pod对象数据
        self.v1 = client.CoreV1Api()
        # k8s_node对象集合
        self.k8s_nodes = get_k8s_object.k8s_nodes_available(only_name=False, is_edge=True)
        # k8s_node_name集合
        self.k8s_nodes_name = get_k8s_object.k8s_nodes_available(only_name=True, is_edge=True)
        # 将k8s节点转化为程序中可以识别的节点对象
        self.nodes = convert.convert_all_k8s_nodes_to_my_nodes()
        self.node_pods = get_k8s_object.get_node_pods()
        # 调度器名称
        self.scheduler_name = scheduler_name

    def schedule(self, k8s_pod):
        print(f"---->调度pod:{k8s_pod.metadata.name}<----")
        t0 = convert.convert_k8s_pod_to_my_pod(k8s_pod)
        # 刘长远
        # chosen_node = self.lcy(t0)
        # KCSS
        chosen_node = self.KCSS(t0)
        # 绑定
        chosen_node = self.nodes[chosen_node.metadata.name]
        self.place_pod(k8s_pod, chosen_node)
        # 记录结果
        nodes = get_k8s_object.k8s_nodes_available(only_name=False, is_edge=True)
        rpd_list = []
        node_cpu_use = dict()
        node_mem_use = dict()
        for i in nodes:
            rpd_list.append(self.get_node_rpd(i))
        variance = np.var(rpd_list)
        nodes_cpu = monitor.http_get_node_free_rate_monitor("cpu")
        nodes_mem = monitor.http_get_node_free_rate_monitor("mem")
        for node_name, val in nodes_cpu.items():
            node_cpu_use[node_name] = 1 - val
            node_mem_use[node_name] = 1 - nodes_mem[node_name]
        with open("output.txt", "a") as f:
            old_stdout = sys.stdout
            sys.stdout = f
            print(f"节点cpu利用率:: {node_cpu_use} 内存利用率:: {node_mem_use}")
            print("---->各节点相似度相对差异<----")
            print(f"rpd_list:: {rpd_list}")
            print(f"pod::{t0.name} 部署后集群相似度相对差异方差:: {variance}")
            print("---->节点资源利用率<----")
            print("------------------------------------")
            sys.stdout = old_stdout  # 恢复原来的stdout



    def KCSS(self, t0):
        nodes = self.k8s_nodes
        DM = []
        chosen_node = None
        for i in nodes:
            DM_temp = []
            http_cpu_rate = (1 - monitor.http_get_node_free_rate_monitor("cpu")[i.metadata.name]) * 100
            http_mem_rate = (1 - monitor.http_get_node_free_rate_monitor("mem")[i.metadata.name]) * 100
            http_disk_rate = monitor.http_get_node_disk_rate_monitor()[i.metadata.name] * 100
            pod_cnt = len(self.node_pods[i.metadata.name])
            DM_temp.append(http_cpu_rate)
            DM_temp.append(http_mem_rate)
            DM_temp.append(http_disk_rate)
            DM_temp.append(pod_cnt)
            print(DM_temp)
            DM.append(DM_temp)
        print(DM)
        rows, cols = len(DM), len(DM[0])  # 获取行数和列数
        gui_yi_DM = [[0] * cols for _ in range(rows)]

        # 计算归一化矩阵
        for j in range(cols):
            temp_sum = math.sqrt(sum(DM[i][j] ** 2 for i in range(rows)))  # 计算每一列的平方和的平方根
            for i in range(rows):
                if temp_sum != 0:
                    gui_yi_DM[i][j] = DM[i][j] / temp_sum  # 每个元素归一化

        print(f"归一化DM：{gui_yi_DM}")

        # 计算加权归一化决策矩阵（这里的权重是均匀的，每个权重为1/4）
        WNDM = [[val / cols for val in row] for row in gui_yi_DM]

        print(f"WNDM：{WNDM}")

        # 计算正理想解（A+）和负理想解（A-）
        A_jia = []
        A_jian = []

        for j in range(3):  # 处理效益型指标
            da = max(WNDM[i][j] for i in range(rows))
            xiao = min(WNDM[i][j] for i in range(rows))
            A_jia.append(da)
            A_jian.append(xiao)

        for j in range(4):  # 处理成本型指标
            da = min(WNDM[i][j] for i in range(rows))
            xiao = max(WNDM[i][j] for i in range(rows))
            A_jia.append(da)
            A_jian.append(xiao)

        print(f"A+：{A_jia}")
        print(f"A-：{A_jian}")

        # 计算每个方案与正理想解和负理想解的距离
        SM_jia = []
        SM_jian = []

        for i in range(rows):
            SM_i_jia = math.sqrt(sum((WNDM[i][j] - A_jia[j]) ** 2 for j in range(cols)))
            SM_i_jian = math.sqrt(sum((WNDM[i][j] - A_jian[j]) ** 2 for j in range(cols)))
            SM_jia.append(SM_i_jia)
            SM_jian.append(SM_i_jian)

        print(f"SM+：{SM_jia}")
        print(f"SM-：{SM_jian}")

        # 计算相对接近度RC
        RC = [SM_jian[i] / (SM_jia[i] + SM_jian[i]) for i in range(rows)]

        print(f"RC：{RC}")

        # 找出RC列表中最大的值的索引
        max_index = RC.index(max(RC))

        print(f"最大的RC值索引：{max_index}")

        for i in nodes:
            last_digit = int(''.join(filter(str.isdigit, i.metadata.name))[-1])
            if last_digit == max_index + 1:
                chosen_node = i
                break
        return chosen_node

    def lcy(self, t0):
        # k8s_node对象集合
        nodes = self.k8s_nodes
        # 集群上是否有短期任务标志
        short_flag = 0
        chosen_node = None
        short_pod_list = self.get_short_pod_of_all_node()
        if len(short_pod_list) != 0:
            short_flag = 1
        if t0.load == 1:
            print(f"pod: {t0.name} 执行时间 : {t0.execution_time}")
            if short_flag == 0:
                print("t0为短期任务，且集群上没有已存在的短期任务，按长期任务部署模式部署")
            else:
                print("t0为短期任务，且集群上有已存在的短期任务")
        else:
            print("t0为长期任务")
        # 长任务或没有短任务
        if t0.load == 0 or short_flag == 0:
            variance_tao_min = 999
            for i in nodes:
                rpd_i_tao_t0 = self.get_node_rpd_tao(i, t0, have_t0=True)
                rpd_else = []
                for j in nodes:
                    if j != i:
                        rpd_else.append(self.get_node_rpd_tao(j))
                rpd_else.append(rpd_i_tao_t0)
                variance_tao = np.var(rpd_else)
                print(f"尝试节点：{i.metadata.name}，集群资源差异度：{variance_tao}")
                if variance_tao < variance_tao_min:
                    variance_tao_min = variance_tao
                    chosen_node = i
            print(f"选择的节点:{chosen_node.metadata.name} 集群资源差异度:{variance_tao_min}")
        # 短期任务负载
        else:
            chosen_flag = False
            rpd_list = []
            for i in nodes:
                rpd_list.append(self.get_node_rpd(i))
            variance_before = np.var(rpd_list)
            print(f"部署前的集群资源差异度:: {variance_before}")
            bind_node = None
            variance_best = 999
            for i in nodes:
                rpd_i_t0 = self.get_node_rpd(i, t0, have_t0=True)
                rpd_else = []
                for j in nodes:
                    if j != i:
                        rpd_else.append(self.get_node_rpd(j))
                rpd_else.append(rpd_i_t0)
                variance = np.var(rpd_else)
                print(f"尝试节点：{i.metadata.name}，集群资源差异度：{variance}")
                if variance < variance_best:
                    bind_node = i
                    variance_best = variance
            if variance_best < variance_before:
                chosen_node = bind_node
                chosen_flag = True
                print("---->存在短期任务部署后负载更均衡的节点<----")
                print(f"chosen_node:: {chosen_node.metadata.name} 集群资源差异度 ::{variance_best} 负载不均衡时间:: 0")
                print("---------------------------------")

            if not chosen_flag:
                # 直接部署让负载均衡变差的情况，考虑负载不均衡时间
                print(f"---->计算负载不均衡时间<----")
                gap_time = self.get_gap_time(t0)
                print(f"gap_time:: {gap_time}")
                if gap_time is None or len(gap_time) == 0:
                    chosen_node = self.choose_one_node(t0)
                    print("---->没有剩余运行时间小于t0的任务<-----")
                    print(f"chosen_node:: {chosen_node.metadata.name} 负载不均衡时间:{t0.execution_time}")
                    print("---------------------------------")
                else:
                    for p in gap_time:
                        variance_best = 999
                        bind_node = None
                        for i in nodes:
                            rpd_i_p_t0 = self.get_node_rpd_p(p, i, t0, have_t0=True)
                            rpd_else = []
                            for j in nodes:
                                if j != i:
                                    rpd_else.append(self.get_node_rpd_p(p, j))
                            rpd_else.append(rpd_i_p_t0)
                            variance_p = np.var(rpd_else)
                            print(f"尝试节点：{i.metadata.name}，{p}时刻后集群资源差异度：{variance_p}")
                            if variance_p < variance_best:
                                variance_best = variance_p
                                bind_node = i
                        if variance_best < variance_before:
                            chosen_node = bind_node
                            print("---->存在最小负载不均衡时间<----")
                            print(f"chosenNode:{chosen_node.metadata.name} 负载不均衡时间::{p}")
                            print("---------------------------------")
                            break

                    if chosen_node is None:
                        chosen_node = self.choose_one_node(t0)
                        print("---->没有负载更均衡的节点，直接根据当前资源负载均衡选择节点<----")
                        print(f"chosenNode:{chosen_node.metadata.name} 负载不均衡时间::{t0.execution_time}")
                        print("---------------------------------")

        return chosen_node

    def bind(self, k8s_pod, node_name, namespace=custom_config.NAMESPACE):
        target = client.V1ObjectReference(api_version='v1', kind='Node', name=node_name)
        meta = client.V1ObjectMeta()
        meta.name = k8s_pod.metadata.name
        body = client.V1Binding(target=target, metadata=meta)
        print(f"---->绑定pod:: {k8s_pod.metadata.name} 节点:: {node_name}<----")
        try:
            api_response = self.v1.create_namespaced_pod_binding(name=k8s_pod.metadata.name, namespace=namespace,
                                                                 body=body, _preload_content=False)
            print("绑定成功")
            return api_response
        except Exception as e:
            print("调用CoreV1Api->create_namespaced_pod_binding时发出警告: %s\n" % e)
            pass

    def place_pod(self, k8s_pod, node):
        self.bind(k8s_pod, node.name, custom_config.NAMESPACE)
        self.node_pods[node.name].append(convert.convert_k8s_pod_to_my_pod(k8s_pod))

    # 删pod的更新
    def update_node_pods(self, k8s_pod):
        removed_pod = convert.convert_k8s_pod_to_my_pod(k8s_pod)
        print(f"---->删除pod:: {removed_pod.name}<----")
        plist = self.node_pods[removed_pod.node]
        for p in plist:
            if p.name == removed_pod.name:
                plist.pop(plist.index(p))
        self.node_pods[removed_pod.node] = plist

    # 获取所有节点上的短期任务
    def get_short_pod_of_all_node(self):
        node_names = self.k8s_nodes_name
        pod_list = []
        for node_name in node_names:
            pods = self.node_pods[node_name]
            for pod in pods:
                if pod.load == 1:
                    pod_list.append(pod)
        return pod_list

    # 获取指定节点上的短期任务，并返回tao、cpu、mem总需求
    def get_short_pod_of_node(self, node_name):
        pods = self.node_pods[node_name]
        tao = 0
        total_cpu = 0
        total_mem = 0
        pod_list = []
        for pod in pods:
            if pod.load == 1:
                pod_list.append(pod)
                tao = max(tao, pod.execution_time)
                total_cpu += pod.cpu_request
                total_mem += pod.memory_request
        return pod_list, tao, total_cpu, total_mem

    def get_node_rpd_tao(self, k8s_node, t0=None, have_t0=False):
        _, tao, total_cpu, total_mem = self.get_short_pod_of_node(k8s_node.metadata.name)
        node = self.nodes[k8s_node.metadata.name]
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
        occupy_cpu_tao = occupy_cpu - total_cpu
        occupy_mem_tao = occupy_mem - total_mem
        r_tao_cpu = occupy_cpu_tao / node.capacity_cpu
        r_tao_mem = occupy_mem_tao / node.capacity_memory
        r_avg_tao = (r_tao_mem + r_tao_cpu) / 2
        rpd_tao = abs(r_tao_cpu - r_tao_mem) / r_avg_tao
        return rpd_tao

    # 当前时间的p秒后节点的rpd
    def get_node_rpd_p(self, p, k8s_node, t0=None, have_t0=False):
        node = self.nodes[k8s_node.metadata.name]
        pods = self.node_pods[k8s_node.metadata.name]
        freed_cpu = 0
        freed_mem = 0
        http_cpu_occupy = (1 - monitor.http_get_node_free_rate_monitor("cpu")[node.name]) * node.capacity_cpu
        http_mem_occupy = (1 - monitor.http_get_node_free_rate_monitor("mem")[node.name]) * node.capacity_memory
        for pod in pods:
            now = convert.convert_to_timestamp(datetime.datetime.now())
            left_time = pod.execution_time - (now - pod.start_time)
            if left_time < p:
                freed_cpu += pod.cpu_request
                freed_mem += pod.memory_request
        # print(node.name)
        if have_t0:
            # print("have_t0")
            occupy_cpu_p = http_cpu_occupy + t0.cpu_request - freed_cpu
            occupy_mem_p = http_mem_occupy + t0.memory_request - freed_mem
        else:
            # print("have_no_t0")
            occupy_cpu_p = http_cpu_occupy - freed_cpu
            occupy_mem_p = http_mem_occupy - freed_mem
        # print(f"node:: {k8s_node.metadata.name} occupy_cpu_{p}:: {occupy_cpu_p}")
        # print(f"node:: {k8s_node.metadata.name} occupy_mem_{p}:: {occupy_mem_p}")
        r_cpu_p = occupy_cpu_p / node.capacity_cpu
        r_mem_p = occupy_mem_p / node.capacity_memory
        r_avg_p = (r_mem_p + r_cpu_p) / 2
        rpd_p = abs(r_cpu_p - r_mem_p) / r_avg_p
        return rpd_p

    def get_node_rpd(self, k8s_node, t0=None, have_t0=False):
        node = self.nodes[k8s_node.metadata.name]
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

    def get_gap_time(self, t0):
        nodes = self.k8s_nodes
        short_pods_time = []
        for i in nodes:
            short_pods, _, _, _ = self.get_short_pod_of_node(i.metadata.name)
            if short_pods:
                for pod in short_pods:
                    now = convert.convert_to_timestamp(datetime.datetime.now())
                    left_time = pod.execution_time - (now - pod.start_time)
                    print(f"pod:{pod.name}，left_time:: {left_time}")
                    if left_time <= t0.execution_time:
                        short_pods_time.append(left_time)
        # 不存在时间小于t0的pod，返回的short_pods_time是None，此时负载不均衡时间为t0的时间
        if len(short_pods_time) == 0:
            return None
        short_pods_time.sort()
        print(short_pods_time)
        step = (short_pods_time[-1] - short_pods_time[0]) / 3
        return [short_pods_time[0] + step, short_pods_time[0] + 2 * step, short_pods_time[-1]]

    def choose_one_node(self, t0):
        nodes = self.k8s_nodes
        chosen_node = None
        variance_tao_min = 999
        for i in nodes:
            rpd_i_tao_t0 = self.get_node_rpd_tao(i, t0, have_t0=True)
            rpd_else = []
            for j in nodes:
                if j != i:
                    rpd_else.append(self.get_node_rpd_tao(j))
            rpd_else.append(rpd_i_tao_t0)
            variance_tao = np.var(rpd_else)
            if variance_tao < variance_tao_min:
                variance_tao_min = variance_tao
                chosen_node = i
        return chosen_node

    # 移除已完成的短期任务
    def remove_pod(self, pod_name, wait_time):
        time.sleep(wait_time)
        try:
            self.v1.delete_namespaced_pod(pod_name, "k8s")
        except ApiException as e:
            print("调用CoreV1Api->delete_namespaced_pod时发出警告: %s\n" % e)