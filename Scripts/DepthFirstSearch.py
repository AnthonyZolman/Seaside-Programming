# Graph represented as an adjacency list
graph = {
   'A': ['B', 'C'],
   'B': ['D', 'E'],
   'C': ['F'],
   'D': [],
   'E': ['F'],
   'F': []
}
def dfs_recursive(graph, node, visited=None):
   if visited is None:
       visited = set()
   visited.add(node)
   print(node) # Process the current node
   for neighbor in graph[node]:
       if neighbor not in visited:
           dfs_recursive(graph, neighbor, visited)
# Start DFS from node 'A'
dfs_recursive(graph, 'B')