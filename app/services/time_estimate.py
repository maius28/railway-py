import heapq
# 图形绘制，上线时可移除
import matplotlib.pyplot as plt 
import networkx as nx
import json


class Graph:
    """
    有向无环图(DAG)类，用于表示和处理任务网络
    每个节点代表一个任务，每条边代表任务间的依赖关系和预计执行时间
    """

    def __init__(self, n):
        """
        初始化图
        n: 节点数量
        """
        self.n = n
        # 邻接表存储图结构，格式为 {节点: [(目标节点, 权重, 是否完成)]}
        self.graph = {i: [] for i in range(n)}
        # 存储每个节点的入度(前置依赖数量)
        self.num_in = {i: 0 for i in range(n)}

    def add_edge(self, u, v, weight):
        """
        添加边 (u -> v)，仅当 u < v 时添加
        u: 源节点
        v: 目标节点
        weight: 边的权重(预计执行时间)
        """
        if u < v:
            self.graph[u].append((v, weight, False))
            self.num_in[v] += 1

    def remove_edge(self, u, v):
        """
        移除边 (u -> v)
        u: 源节点
        v: 目标节点
        """
        self.graph[u] = [(node, w, completed) for node, w, completed in self.graph[u] if node != v]
        self.num_in[v] -= 1

    def input_real(self, u, v, real_weight):
        """
        更新边的实际权重并标记为已完成
        仅当源节点入度为0且目标节点入度不为0时允许更新
        u: 源节点
        v: 目标节点
        real_weight: 实际权重
        """
        if self.num_in[u] == 0 and self.num_in[v] != 0:
            for i, (node, weight, completed) in enumerate(self.graph[u]):
                if node == v:
                    self.graph[u][i] = (v, real_weight, True)
                    self.num_in[v] -= 1
                    print(f"Edge {u} -> {v} updated with weight {real_weight} and marked as completed.")
                    return
            print(f"out-degree of {u} is not 0 or Edge {u} -> {v} not found.")
        else:
            if self.num_in[v] == 0:
                print(f"目标节点 {v} 的 out-degree 为 0，不允许更新该边权重。")
            else:
                print(f"起始节点 {u} 的 out-degree 不为 0 或边 {u} -> {v} 未找到。")

    def dijkstra(self, start, end):
        """
        使用Dijkstra算法计算从start到end的最长路径
        由于Dijkstra适用于最短路径，这里通过取负权重转换为最长路径问题
        start: 起始节点
        end: 结束节点
        返回: (最长路径长度, 最长路径节点列表)
        """
        # 初始化距离数组为负无穷大
        dist = [-float('inf')] * len(self.graph)
        # 节点索引映射
        node_indices = sorted(self.graph.keys())
        index_mapping = {node: idx for idx, node in enumerate(node_indices)}
        dist[index_mapping[start]] = 0
        # 优先队列 (距离的负值, 节点)
        pq = [(-0, start)]
        # 前驱节点记录
        pre = {node: None for node in self.graph}

        while pq:
            d, u = heapq.heappop(pq)
            d = -d  # 恢复实际距离

            if d < dist[index_mapping[u]]:
                continue

            # 遍历所有邻接节点
            for v, weight, completed in self.graph[u]:
                new_dist = dist[index_mapping[u]] + weight
                if new_dist > dist[index_mapping[v]]:
                    dist[index_mapping[v]] = new_dist
                    pre[v] = u
                    heapq.heappush(pq, (-new_dist, v))

        # 回溯构建最长路径
        longest_path = []
        cur = end
        while cur is not None:
            longest_path.append(cur)
            cur = pre[cur]
        longest_path.reverse()
        return dist[index_mapping[end]], longest_path

    def remove_node(self, node):
        """
        移除节点及其所有关联边
        同时递归移除因该节点移除而导致入度为0的后续节点
        node: 要移除的节点
        """
        # 移除所有指向该节点的边
        for u in self.graph:
            original_edges = self.graph[u]
            new_edges = []
            for v, weight, completed in original_edges:
                if v == node:
                    continue
                new_edges.append((v, weight, completed))
            self.graph[u] = new_edges

        # 处理该节点的后续节点
        if node in self.graph:
            for v, _, _ in self.graph[node]:
                if v in self.num_in:
                    self.num_in[v] -= 1
                    # 递归移除入度为0的后续节点
                    if self.num_in[v] == 0:
                        self.remove_node(v)
            del self.graph[node]

        if node in self.num_in:
            del self.num_in[node]

    def change_edge_weight(self, u, v, new_weight, json_data, node_name_mapping):
        """
        修改边的权重
        不允许修改目标节点为分支选择类型的边权重
        u: 源节点
        v: 目标节点
        new_weight: 新权重
        json_data: JSON数据
        node_name_mapping: 节点名称到索引的映射
        """
        target_node_name = [name for name, idx in node_name_mapping.items() if idx == v][0]
        if json_data[target_node_name].get('type') == 'branch_selection':
            print(f"目标节点 {target_node_name} 是分支选择节点，不允许修改边权重。")
            return
        for i, (node, weight, completed) in enumerate(self.graph[u]):
            if node == v:
                self.graph[u][i] = (v, new_weight, completed)
                print(f"Edge {u} -> {v} updated with new weight {new_weight}.")
                return
        print(f"Edge {u} -> {v} not found.")


def parse_json_to_graph(json_file):
    """
    从JSON文件解析数据并构建图
    json_file: JSON文件路径
    返回: (图对象, 节点名称列表)
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        nodes = list(data.keys())
        node_index = {node: i for i, node in enumerate(nodes)}
        graph = Graph(len(nodes))

        # 构建图结构
        for node, info in data.items():
            u = node_index[node]
            next_nodes = info.get('next', [])
            if isinstance(next_nodes, str):
                next_nodes = [next_nodes]
            for next_node in next_nodes:
                v = node_index[next_node]
                next_info = data[next_node]
                predict_time = next_info['predict_time']
                weight = parse_time(predict_time)
                graph.add_edge(u, v, weight)

            # 处理分支选择节点
            if 'options' in info:
                for option, next_node in info['options'].items():
                    if isinstance(next_node, list):
                        for sub_next_node in next_node:
                            v = node_index[sub_next_node]
                            next_info = data[sub_next_node]
                            predict_time = next_info['predict_time']
                            weight = parse_time(predict_time)
                            graph.add_edge(u, v, weight)
                    else:
                        v = node_index[next_node]
                        next_info = data[next_node]
                        predict_time = next_info['predict_time']
                        weight = parse_time(predict_time)
                        graph.add_edge(u, v, weight)

        return graph, nodes
    except FileNotFoundError:
        print(f"Error: File {json_file} not found.")
        return None, None


def parse_time(predict_time):
    """
    将时间字符串转换为秒数
    支持格式如"30s", "2min", "1.5h"
    predict_time: 时间字符串
    返回: 对应的秒数(float类型)
    """
    if 's' in predict_time:
        return float(predict_time.replace('s', ''))
    elif 'min' in predict_time:
        return float(predict_time.replace('min', '')) * 60
    elif 'h' in predict_time:
        return float(predict_time.replace('h', '')) * 3600
    return float(predict_time)


def plot_graph(graph, node_names, selected_nodes):
    """
    可视化图结构，高亮显示最长路径
    graph: 图对象
    node_names: 节点名称列表
    selected_nodes: 要显示的节点列表
    """
    G = nx.DiGraph()
    # 构建用于可视化的子图
    for u in selected_nodes:
        for v, weight, completed in graph.graph[u]:
            if v in selected_nodes:
                G.add_edge(u, v, weight=weight, completed=completed)

    # 找出入度为0的节点(已完成节点)
    zero_out_node = [node for node, num_in in graph.num_in.items() if num_in == 0 and node in selected_nodes]
    start = min(selected_nodes)
    end = max(selected_nodes)
    longest_path_len, longest_path = graph.dijkstra(start, end)

    # 找出最长路径中入度最大的节点(关键路径上的关键节点)
    max_num_in = -1
    max_node = None
    end_index = node_names.index('END') if 'END' in node_names else None
    for node in longest_path:
        if end_index is not None and node == end_index:
            continue
        if graph.num_in[node] > max_num_in:
            max_num_in = graph.num_in[node]
            max_node = node

    # 使用shell布局算法
    pos = nx.shell_layout(G)

    # 绘制图
    plt.figure(figsize=(12, 10))
    nx.draw(G, pos, with_labels=True, labels={i: node_names[i] for i in selected_nodes},
            node_color='lightblue', node_size=500, font_size=12, font_weight='bold', arrows=True)

    # 高亮最长路径
    longest_path_edges = [(longest_path[i], longest_path[i + 1]) for i in range(len(longest_path) - 1)]
    nx.draw_networkx_edges(G, pos, edgelist=longest_path_edges, edge_color='red', arrows=True)

    # 显示边权重
    edge_labels = {(u, v): G[u][v]['weight'] for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

    # 添加注释信息
    plt.annotate(
        f"Longest Path Length: {longest_path_len} seconds\nFinished nodes: {[node_names[node] for node in zero_out_node]}\nKey Point: {node_names[max_node]},num_in: {max_num_in}",
        xy=(0.5, 0.04), xycoords='axes fraction', fontsize=12, ha='center', va='center')
    plt.title("Graph Visualization (DAG) with Edge Weights - Non-overlapping")
    plt.show()


def get_selected_nodes(graph, node_names, current_node, json_data, node_name_mapping):
    """
    处理分支选择节点，获取用户选择的路径
    graph: 图对象
    node_names: 节点名称列表
    current_node: 当前节点
    json_data: 原始JSON数据
    node_name_mapping: 节点名称到索引的映射
    返回: 更新后的节点列表
    """
    successors = [v for v, _, _ in graph.graph[current_node]]
    for succ in successors:
        succ_name = node_names[succ]
        if json_data[succ_name].get('type') == 'branch_selection':
            print(f"后续节点 {succ_name} 是分支选择节点，请选择后续节点:")
            options = json_data[succ_name].get('options', {})
            for option, next_node in options.items():
                if isinstance(next_node, list):
                    print(f"{option}: {', '.join(next_node)}")
                else:
                    print(f"{option}: {next_node}")

            # 获取用户选择
            while True:
                choice = input("请输入你的选择: ")
                if choice in options:
                    selected_next_node = options[choice]
                    if isinstance(selected_next_node, list):
                        while True:
                            print("该选项有多个后续节点，请选择其中一个:")
                            for idx, node in enumerate(selected_next_node):
                                print(f"{idx + 1}. {node}")
                            try:
                                sub_choice = int(input("请输入你的选择 (数字): ")) - 1
                                if 0 <= sub_choice < len(selected_next_node):
                                    final_next_node = selected_next_node[sub_choice]
                                    break
                                else:
                                    print("无效的选择，请重新输入。")
                            except ValueError:
                                print("输入无效，请输入一个数字。")
                    else:
                        final_next_node = selected_next_node
                    break
                else:
                    print("无效的选择，请重新输入。")

            # 更新图结构
            for i, (node, _, _) in enumerate(graph.graph[current_node]):
                if node == succ:
                    graph.graph[current_node][i] = (node, graph.graph[current_node][i][1], True)
                    graph.num_in[succ] -= 1

            # 移除未选择的路径
            for option, next_node in options.items():
                if isinstance(next_node, list):
                    for node in next_node:
                        if node != final_next_node:
                            next_node_index = node_name_mapping[node]
                            if graph.num_in[next_node_index] == 1:
                                graph.remove_edge(succ, next_node_index)
                                graph.remove_node(next_node_index)
                            else:
                                graph.remove_edge(succ, next_node_index)
                else:
                    if next_node != final_next_node:
                        next_node_index = node_name_mapping[next_node]
                        if graph.num_in[next_node_index] == 1:
                            graph.remove_edge(succ, next_node_index)
                            graph.remove_node(next_node_index)
                        else:
                            graph.remove_edge(succ, next_node_index)

            # 重新绘制图
            plot_graph(graph, node_names, list(graph.graph.keys()))
            # 继续检查分支选择
            check_branch_selection(graph, node_names, json_data, node_name_mapping)
    return list(graph.graph.keys())


def check_branch_selection(graph, node_names, json_data, node_name_mapping):
    """
    检查是否存在需要处理的分支选择节点
    graph: 图对象
    node_names: 节点名称列表
    json_data: 原始JSON数据
    node_name_mapping: 节点名称到索引的映射
    返回: 是否存在分支选择节点
    """
    zero_out_nodes = [node for node, num_in in graph.num_in.items() if num_in == 0]
    has_branch_selection = False
    for node in zero_out_nodes:
        successors = [v for v, _, _ in graph.graph[node]]
        for succ in successors:
            succ_name = node_names[succ]
            if graph.num_in[succ] != 0 and json_data[succ_name].get('type') == 'branch_selection':
                print(f"由于节点 {node_names[node]} 的后续节点 {succ_name} 是分支选择节点，请进行选择:")
                get_selected_nodes(graph, node_names, node, json_data, node_name_mapping)
                has_branch_selection = True
    return has_branch_selection


def main():
    """
    主函数，程序入口点
    程序运行流程:
        1. 从"铁路外部人员入侵线路.json"文件加载图数据
        2. 初始化并显示图
        3. 进入交互循环，提供以下选项:
           - 输入起始节点名称和目标节点名称，更新边的实际权重
           - 输入"change"，修改边的权重
           - 输入"q"，退出程序
        4. 当遇到分支选择节点时，自动提示用户进行选择
        5. 每次更新后重新计算并显示最长路径
        6. 当最后一个节点的所有前置节点都完成时，程序结束
    用户输入示例:
        请输入边的起始节点名称（输入 'q' 退出，输入 'change' 修改边权重）: A
        请输入边的目标节点名称: B
        请输入该边的实际权重（秒）: 100

    当且仅当END节点的所有前序节点的num_out为0时，程序结束
    """
    graph, node_names = parse_json_to_graph('铁路外部人员入侵线路.json')
    if graph is None or node_names is None:
        return
    node_name_mapping = {name: i for i, name in enumerate(node_names)}
    json_data = json.load(open('铁路外部人员入侵线路.json', 'r', encoding='utf-8'))

    # 初始显示图
    plot_graph(graph, node_names, list(graph.graph.keys()))

    if 'END' not in node_names:
        print("没有END节点")
        return

    # 主交互循环
    while True:
        # 检查是否有分支选择需要处理
        has_branch_selection = check_branch_selection(graph, node_names, json_data, node_name_mapping)
        if has_branch_selection:
            continue

        # 用户输入选项
        source = input("请输入边的起始节点名称（输入 'q' 退出，输入 'change' 修改边权重）: ")
        if source.lower() == 'q':
            break
        if source.lower() == 'change':
            # 修改边权重模式
            source_node = input("请输入起始节点名称: ")
            if source_node not in node_names:
                print("输入的起始节点名称不存在，请重新输入。")
                continue
            target_node = input("请输入目标节点名称: ")
            if target_node not in node_names:
                print("输入的目标节点名称不存在，请重新输入。")
                continue
            u = node_name_mapping[source_node]
            v = node_name_mapping[target_node]
            try:
                new_weight = float(input("请输入新的边权重（秒）: "))
            except ValueError:
                print("输入的权重不是有效的数字，请重新输入。")
                continue
            graph.change_edge_weight(u, v, new_weight, json_data, node_name_mapping)
        elif source not in node_names:
            print("输入的起始节点名称不存在，请重新输入。")
            continue
        else:
            # 更新实际权重模式
            target = input("请输入边的目标节点名称: ")
            if target not in node_names:
                print("输入的目标节点名称不存在，请重新输入。")
                continue

            u = node_name_mapping[source]
            v = node_name_mapping[target]

            # 检查边是否存在
            edge_exists = False
            for node, _, _ in graph.graph[u]:
                if node == v:
                    edge_exists = True
                    break

            if not edge_exists:
                print(f"边 {source} -> {target} 不存在，请重新输入。")
                continue

            # 获取实际权重并更新
            try:
                real_weight = float(input("请输入该边的实际权重（秒）: "))
            except ValueError:
                print("输入的权重不是有效的数字，请重新输入。")
                continue

            graph.input_real(u, v, real_weight)

        # 计算并显示最长路径
        start = min(graph.graph.keys())
        end = max(graph.graph.keys())
        longest_path_len, longest_path = graph.dijkstra(start, end)
        print(f"更新边权重后，最长路径长度: {longest_path_len} seconds")
        print(f"更新边权重后，最长路径: {[node_names[node] for node in longest_path]}")

        # 重新绘制图
        plot_graph(graph, node_names, list(graph.graph.keys()))

        # 检查是否所有前置节点都已完成
        last_node = max(graph.graph.keys())
        predecessors = []
        for node in graph.graph:
            for v, _, _ in graph.graph[node]:
                if v == last_node:
                    predecessors.append(node)

        all_predecessors_zero = True
        for pred in predecessors:
            if graph.num_in[pred] != 0:
                all_predecessors_zero = False
                break

        if all_predecessors_zero:
            print("最后一个节点的所有前续节点的 num_in 都为 0，程序结束。")
            break


if __name__ == "__main__":
    main()