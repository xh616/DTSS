class Node(object):
    def __init__(self, ip, name, k8s_node, capacity_cpu, allocatable_cpu, capacity_memory,
                 allocatable_memory):
        self.ip = ip
        # 节点名称
        self.name = name
        # k8s_node对象
        self.k8s_node = k8s_node
        # 节点cpu总量
        self.capacity_cpu = capacity_cpu
        # 节点cpu可用量
        self.allocatable_cpu = allocatable_cpu
        # 节点内存总容量
        self.capacity_memory = capacity_memory
        # 节点内存的可用容量
        self.allocatable_memory = allocatable_memory
