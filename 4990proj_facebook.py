from mpi4py import MPI
import networkx as nx
import heapq
import math
import time
import csv

def calculate_distances(graph, starting_vertex):
    distances = {vertex: float('infinity') for vertex in graph}
    distances[starting_vertex] = 0

    pq = [(0, starting_vertex)]
    while len(pq) > 0:
        current_distance, current_vertex = heapq.heappop(pq)

        # Nodes can get added to the priority queue multiple times. We only
        # process a vertex the first time we remove it from the priority queue.
        if current_distance > distances[current_vertex]:
            continue

        for neighbor, weight in graph[current_vertex].items():
            distance = current_distance + weight

            # Only consider this new path if it's better than any path we've
            # already found.
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))

    return distances

# setting up the communicator
comm = MPI.COMM_WORLD

rank = comm.Get_rank()
size = comm.Get_size()

# introduce MPI calls here
start_time = time.time()
if rank == 0:
    # G = nx.karate_club_graph()
    # TWITTER DATASET
    # G = nx.read_edgelist("twitter_combined.txt", create_using=nx.DiGraph)
    # WIKI-VOTE DATASET
    # G = nx.read_edgelist("Wiki-Vote.txt", create_using=nx.DiGraph)
    # FACEBOOK DATASET
    # generate list of nodes
    node_names = []
    for x in range(22470):
        node_names.append(x)

    # Read in the edgelist file
    with open('musae_facebook_edges.csv', 'r') as edgecsv:
        edgereader = csv.reader(edgecsv)
        edges = [tuple(e) for e in edgereader][1:]

    G = nx.Graph()  # Initialize a Graph object
    G.add_nodes_from(node_names)  # Add nodes to the Graph
    G.add_edges_from(edges)  # Add edges to the Graph

    numNodes = G.number_of_nodes()
    graphDict = {}
    for n in G.nodes:
        tempDict = {}
        for e in G.edges(n):
            tempDict[e[1]] = 1

        graphDict[n] = tempDict

    # prepping node lists for MPI scatter
    all_nodes = list(G.nodes)
    # divide into chunks
    nodes_subset = [[] for _ in range(size)]
    for i, chunk in enumerate(all_nodes):
        nodes_subset[i % size].append(chunk)
    # print out graph as a dictionary
    # print(graphDict)
else:
    graphDict = None
    nodes_subset = None
    numNodes = None

# MPI calls
graphDict = comm.bcast(graphDict, root=0)
numNodes = comm.bcast(numNodes, root=0)
nodes_subset = comm.scatter(nodes_subset, root=0)

#print(1, calculate_distances(graphDict, 1))
#xDist = calculate_distances(graphDict,1)
cc = []
for source in nodes_subset:
    # Dijkstra's
    xDist = calculate_distances(graphDict, source)
    # closeness centrality calculations
    sum = 0.0
    for k, v in xDist.items():
        if not math.isinf(v):
            sum = sum + v
    if sum != 0:
        cc.append((numNodes - 1) / sum)
    else:
        cc.append(0)
# cross checking
#print(cc)

# gathering all closeness centrality values
cc_vals = comm.gather(cc, root=0)
end_time = time.time()

print("Time taken:", (end_time - start_time))
# if(rank == 0):
    # print(cc_vals)
    # print(nx.closeness_centrality(G))