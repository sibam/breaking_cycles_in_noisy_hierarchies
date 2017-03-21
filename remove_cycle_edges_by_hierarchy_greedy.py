import networkx as nx
from s_c_c import filter_big_scc
from s_c_c import get_big_sccs
from file_io import write_pairs_to_file
from file_io import read_dict_from_file
import os.path
import sys
sys.setrecursionlimit(5500000)


def get_agony(edge,players):
	u,v = edge 
	return max(players[u]-players[v],0)

def get_agonies(edges,players):
	edges_agony_dict = {}
	for edge in edges:
		edges_agony_dict[edge] = get_agony(edge,players)
	return edges_agony_dict

def remove_cycle_edges_by_agony(graph,players,edges_to_be_removed):
	
	pair_agony_dict = {}
	for pair in graph.edges_iter():
		u,v = pair
		agony = max(players[u]-players[v],0)
		pair_agony_dict[pair] = agony
	from helper_funs import pick_from_dict
	pair_max_agony,agony = pick_from_dict(pair_agony_dict)

	edges_to_be_removed.append(pair_max_agony)
	#print("edge to be removed: %s, agony: %0.4f" % (pair_max_agony,max_agony))
	sub_graphs = filter_big_scc(graph,[pair_max_agony])
	if sub_graphs:
		num_subs = len(sub_graphs)
		for index,sub in enumerate(sub_graphs):
			#print("%d / %d scc: (%d,%d)" % (index+1,num_subs,sub.number_of_nodes(),sub.number_of_edges()))
			remove_cycle_edges_by_agony(sub,players,edges_to_be_removed)
	else:
		return None


def remove_cycle_edges_by_agony_iterately(sccs,players,edges_to_be_removed):
	while True:
		graph = sccs.pop()
		pair_max_agony = None
		max_agony = -1
		for pair in graph.edges_iter():
			u,v = pair
			agony = max(players[u]-players[v],0)
			if agony >= max_agony:
				pair_max_agony = (u,v)
				max_agony = agony
		edges_to_be_removed.append(pair_max_agony)
		#print("graph: (%d,%d), edge to be removed: %s, agony: %0.4f" % (graph.number_of_nodes(),graph.number_of_edges(),pair_max_agony,max_agony))
		graph.remove_edges_from([pair_max_agony])
		#print("graph: (%d,%d), edge to be removed: %s" % (graph.number_of_nodes(),graph.number_of_edges(),pair_max_agony))
		sub_graphs = filter_big_scc(graph,[pair_max_agony])
		if sub_graphs:
			for index,sub in enumerate(sub_graphs):
				sccs.append(sub)
		if not sccs:
			return

def scores_of_nodes_in_scc(sccs,players):
	from s_c_c import nodes_in_scc
	scc_nodes = nodes_in_scc(sccs)
	scc_nodes_score_dict = {}
	for node in scc_nodes:
		scc_nodes_score_dict[node] = players[node]
	#print("# scores of nodes in scc: %d" % (len(scc_nodes_score_dict)))
	return scc_nodes_score_dict

def scc_based_to_remove_cycle_edges_recursilvely(g,nodes_score):
	big_sccs = get_big_sccs(g)
	scc_nodes_score_dict = scores_of_nodes_in_scc(big_sccs,nodes_score)

	edges_to_be_removed = []
	for sub in big_sccs:
		scc_edges_to_be_removed = []
		remove_cycle_edges_by_agony(sub,scc_nodes_score_dict,scc_edges_to_be_removed)
		edges_to_be_removed += scc_edges_to_be_removed
	#print(" # edges to be removed: %d" % len(edges_to_be_removed))
	return edges_to_be_removed


def scc_based_to_remove_cycle_edges_iterately(g,nodes_score):
	big_sccs = get_big_sccs(g)
	scc_nodes_score_dict = scores_of_nodes_in_scc(big_sccs,nodes_score)
	edges_to_be_removed = []
	remove_cycle_edges_by_agony_iterately(big_sccs,scc_nodes_score_dict,edges_to_be_removed)
	#print(" # edges to be removed: %d" % len(edges_to_be_removed))
	return edges_to_be_removed

def remove_cycle_edges(graph_file,players_score):
	return remove_cycle_edges_by_agony(graph_file,players_score)


'''	
def remove_cycle_edges_by_agony(graph_file,players_score):
	if players_score == "socialagony":
		agony_file = graph_file[:len(graph_file)-6] + "_rank.txt"
		if os.path.isfile(agony_file):
			players = read_dict_from_file(agony_file)
		else:
			from compute_social_agony import compute_social_agony
			players = compute_social_agony(graph_file)
	g = nx.read_edgelist(graph_file,create_using = nx.DiGraph(),nodetype = int)
	if players_score == "pagerank":
		players = nx.pagerank(g, alpha = 0.85)
	elif players_score == "trueskill":
		output_file = graph_file[:len(graph_file)-6] + "_trueskill.txt"
		if os.path.isfile(output_file):
			print("load pre-computed trueskill from: %s" % output_file)
			players = read_dict_from_file(output_file,key_type = int, value_type = float)
		else:
			print("start computing trueskill...")
			from true_skill import graphbased_trueskill
			players = graphbased_trueskill(g)
			from file_io import write_dict_to_file
			print("write trueskill to file: %s" % output_file)
			write_dict_to_file(players,output_file)
	edges_to_be_removed = scc_based_to_remove_cycle_edges_iterately(g,players)
	edges_to_be_removed = list(set(edges_to_be_removed))
	
	print("edges to be removed: %s" % edges_to_be_removed)
	#analysis_graph(g)
	#g.remove_edges_from(edges_to_be_removed)
	edges_to_be_removed_file = graph_file[:len(graph_file)-6] + "_removed_by_" + players_score + ".edges"
	write_pairs_to_file(edges_to_be_removed,edges_to_be_removed_file)

	#print("after removal of cycle edges: %d" % len(edges_to_be_removed))
	#analysis_graph(g)
	#import random 
	#index = random.randint(0, len(edges_to_be_removed)-1)
	#g.add_edges_from([edges_to_be_removed[index]])
	#print("analysis of graph after adding an edge back")
	#analysis_graph(g)
	#g.remove_edges_from([edges_to_be_removed[index]])
	return edges_to_be_removed


import argparse
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-g","--graph_file",default= " ", help = "input graph file name (edges list)")
	parser.add_argument("-s","--score",default = "pagerank",help = "nodes score function")
	args = parser.parse_args()
	graph_file = args.graph_file
	players_score = args.score

	edges_to_be_removed = remove_cycle_edges(graph_file,players_score)
	edges_to_be_removed_file = graph_file[:len(graph_file)-6] + "_removed_by_" + players_score + ".edges"
	extra_edges_file = graph_file[:len(graph_file)-6] + "_extra.edges"
	from file_io import write_pairs_to_file
	write_pairs_to_file(edges_to_be_removed,edges_to_be_removed_file)
'''