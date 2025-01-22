import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from code.classes.grid_class import Grid_3D, plot_wires_3d
from code.classes.nodes_class import Node
from code.classes.wire_class import Wire, WirePoint
import pandas as pd
from code.imports import import_netlist, import_nodes
from code.algorithms.a_star import a_star_algorithm
from code.algorithms.DFS import dfs_algorithm as Algorithm
import itertools
import csv

nodes_csv_path = './gates&netlists/chip_2/print_2.csv'
netlist_csv_path = './gates&netlists/chip_2/netlist_9.csv'
nodes_list = import_nodes(nodes_csv_path)
grid_width = max(node._max_value for node in nodes_list) + 1
grid_length = max(node._max_value for node in nodes_list) + 1
functie = Algorithm

# Initiate the grid, and import nodes and netlist
grid = Grid_3D(grid_width, grid_length, nodes_csv_path)
nodes_list = import_nodes(nodes_csv_path)
for node in nodes_list:
    grid.place_node(node)
netlist = import_netlist(netlist_csv_path)
all_wire_runs = []
successful_grid = 0
total_tries = 0

for netlists in itertools.permutations(netlist):
    if total_tries > 20:
        break
    # Reinitialize the grid for each permutation
    grid.clear_wires()
    wires = grid.return_wire_list()  # empty right now

    success_for_this_permutation = True  # a flag we set to false if a route fails

    if len(netlists) == 0:
        raise ValueError("No netlist given.")

    laid_wires = []  # Keep track of successfully laid wires

    # Attempt to form wires for each pair in this permutation
    for i in range(len(netlists)):
        node1_id, node2_id = netlists[i]
        node1 = nodes_list[node1_id - 1]
        node2 = nodes_list[node2_id - 1]

        while True:
            try:
                # Attempt to find a route
                wire = functie(node1, node2, grid, nodes_csv_path, netlist_csv_path)
                if wire is not None:
                    laid_wires.append(wire)  # Add wire to the list of laid wires
                    break  # Exit the loop if the wire is laid successfully
                else:
                    raise Exception("No valid path found")
            except Exception as e:
                # If we fail, backtrack by removing the last wire
                if laid_wires:
                    last_wire = laid_wires.pop()  # Remove the last laid wire
                    grid.remove_wire(last_wire)  # Remove it from the grid
                else:
                    # If no wires to backtrack, mark permutation as failed
                    success_for_this_permutation = False
                    break

        if not success_for_this_permutation:
            break  # Skip the rest of the permutation if any route fails

    # Now we've tried to route all pairs in this permutation (unless we broke early)
    if success_for_this_permutation:
        # This permutation succeeded for all net pairs
        all_wire_runs.append(wires)
        successful_grid += 1

    total_tries += 1
    print(total_tries)

    # Optionally remove the nodes from the wire dict
    grid.remove_nodes_pointdict()

# After trying all permutations
success_percentage = (successful_grid / total_tries) * 100
print(f'{success_percentage}% of the grids were successful')
print(f'{successful_grid} out of {total_tries} permutations were successful')