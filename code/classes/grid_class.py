import matplotlib.pyplot as plt
from collections import Counter

from code.classes.nodes_class import Node
from code.classes.wire_class import Wire, WirePoint
from code.imports import import_netlist, import_nodes
from code.classes.segment_class import Segment

class Grid_3D:
    def __init__(self, n, m, nodes_csv_path):
        """
        Generates a grid of n x m x 8. 
        """
        self.n = n
        self.m = m
        self.height = 8
        self._wires = []
        self._lines_count = 0
        self._wires_segments = set()
        self._nodes = import_nodes(nodes_csv_path)
        self.nodes_csv_path = nodes_csv_path
        self._reserved_points = set()
        self.failed_wires = 0
        self.total_wires = 0
        self._point_dict = {
            (x, y, z): 0
            for x in range(self.n)
            for y in range(self.m)
            for z in range(self.height)
        }
        self.grid_values = {
            (x, y, z): 1 for x in range(self.n) for y in range(self.m) for z in range(self.height)
        }

    def set_point_value(self, wire: Wire, value: int):
        """
        Sets a value for a specific point in the grid.

        Args:
            x (int): X-coordinate of the point.
            y (int): Y-coordinate of the point.
            z (int): Z-coordinate of the point.
            value (int): The value to set for the point.
        """
        wirepoints = wire.give_wirepoints()
        for wirepoint in wirepoints:
            location = wirepoint.give_place()
            self.grid_values[location] += value

    def return_point_dict(self):
        """
        Returns the point dict.
        """
        return self._point_dict

    def get_point_value(self, point: WirePoint) -> int:
        """
        Gets the value of a specific point in the grid.

        Args:
            x (int): X-coordinate of the point.
            y (int): Y-coordinate of the point.
            z (int): Z-coordinate of the point.

        Returns:
            int: The value of the point.
        """
        if 0 <= point.give_x() < self.n and 0 <= point.give_y() < self.m and 0 <= point.give_z() < self.height:
            return self.grid_values[(point.give_x(), point.give_y(), point.give_z())]
        else:
            raise ValueError("Point is out of grid bounds.")
        
    def count_neighbors(self, x, y, z):
        """
        Count the number of valid neighboring cells for a given cell at (x, y, z).

        Parameters:
            x (int): X-coordinate of the cell.
            y (int): Y-coordinate of the cell.
            z (int): Z-coordinate of the cell.

        Returns:
            int: The count of valid neighboring cells.
        """
        neighbor_count = 0
        for dx, dy, dz in [
            (1, 0, 0), (-1, 0, 0),  # Horizontal neighbors
            (0, 1, 0), (0, -1, 0),  # Vertical neighbors
            (0, 0, 1), (0, 0, -1)   # Above and below neighbors
        ]:
            nx, ny, nz = x + dx, y + dy, z + dz

            # Check if the neighbor is within grid boundaries
            if 0 <= nx < self.n and 0 <= ny < self.m and 0 <= nz < self.height:
                neighbor_count += 1
        return neighbor_count

    def apply_costs_around_nodes(self, netlist):
        """
        1) Apply extra cost around nodes that appear frequently in the netlist.
        2) Then, ALSO make outer cells cheaper and center cells more expensive.

        The end result:
        - Heavily used nodes still get big cost in/around them (as before).
        - Among the "non-node" space, cells near the grid edges are cheaper,
        and cells near the center are more expensive.
        """

        # Count how many times each node appears in the netlist
        node_counts = Counter([node for pair in netlist for node in pair])

        # For each node, set certain rings of cells around it to a higher cost
        for node in self._nodes:
            x, y, z = node.give_x(), node.give_y(), 0
            
            # If node used >=5 times, apply big cost
            if node_counts[node] >= 5 or (node_counts[node] >= 4 and self.count_neighbors(x,y,z) <= 4) or (node_counts[node] >= 3 and self.count_neighbors(x,y,z) <= 3):
                for dx, dy, dz, cost in [
                    (0, 0, 1, 150),  # Above
                    (0, -1, 0, 150), (0, 1, 0, 150),  # Vertical neighbors
                    (-1, 0, 0, 150), (1, 0, 0, 150),  # Horizontal neighbors

                    (0, 0, 2, 50),  # Two steps above
                    (0, -2, 0, 50), (0, 2, 0, 50),  # Two steps vertical
                    (-2, 0, 0, 50), (2, 0, 0, 50),  # Two steps horizontal
                    (-1, -1, 0, 50), (-1, 1, 0, 50), (1, 1, 0, 50), (1, -1, 0, 50), # Non direct neighbors bottom layer
                    (1, 0, 1, 50), (-1, 0, 1, 50), (0, -1, 1, 50), (0, 1, 1, 50), # One horizontal one vertical

                    # Now all points with a distance of 3 steps
                    # Pure axis-aligned points
                    (3, 0, 0, 5), (-3, 0, 0, 5), (0, 3, 0, 5), (0, -3, 0, 5), (0, 0, 3, 5),

                    # Two-axis combinations
                    (2, 1, 0, 5), (2, -1, 0, 5), (2, 0, 1, 5),
                    (-2, 1, 0, 5), (-2, -1, 0, 5), (-2, 0, 1, 5),
                    (1, 2, 0, 5), (1, -2, 0, 5), (0, 2, 1, 5),
                    (-1, 2, 0, 5), (-1, -2, 0, 5), (0, -2, 1, 5),
                    (1, 0, 2, 5), (-1, 0, 2, 5), (0, 1, 2, 5), (0, -1, 2, 5),

                    # Three-axis combinations
                    (1, 1, 1, 5), (1, -1, 1, 5), (-1, 1, 1, 5), (-1, -1, 1, 5)
                    ]:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if 0 <= nx < self.n and 0 <= ny < self.m and 0 <= nz < self.height:
                        self.grid_values[(nx, ny, nz)] = cost

            # If node used >=4 times, apply big cost
            if node_counts[node] >= 4 or (node_counts[node] >= 3 and self.count_neighbors(x,y,z) <= 4) or (node_counts[node] >= 2 and self.count_neighbors(x,y,z) <= 3):
                for dx, dy, dz, cost in [
                    (0, 0, 1, 50),  # Above
                    (0, -1, 0, 50), (0, 1, 0, 50),  # Vertical neighbors
                    (-1, 0, 0, 50), (1, 0, 0, 50),  # Horizontal neighbors

                    (0, 0, 2, 25),  # Two steps above
                    (0, -2, 0, 25), (0, 2, 0, 25),  # Two steps vertical
                    (-2, 0, 0, 25), (2, 0, 0, 25),  # Two steps horizontal
                    (-1, -1, 0, 25), (-1, 1, 0, 25), (1, 1, 0, 25), (1, -1, 0, 25), # Non direct neighbors bottom layer
                    (1, 0, 1, 25), (-1, 0, 1, 25), (0, -1, 1, 25), (0, 1, 1, 25), # One horizontal one vertical

                    # Now all points with a distance of 3 steps
                    # Pure axis-aligned points
                    (3, 0, 0, 5), (-3, 0, 0, 5), (0, 3, 0, 5), (0, -3, 0, 5), (0, 0, 3, 5),

                    # Two-axis combinations
                    (2, 1, 0, 5), (2, -1, 0, 5), (2, 0, 1, 5),
                    (-2, 1, 0, 5), (-2, -1, 0, 5), (-2, 0, 1, 5),
                    (1, 2, 0, 5), (1, -2, 0, 5), (0, 2, 1, 5),
                    (-1, 2, 0, 5), (-1, -2, 0, 5), (0, -2, 1, 5),
                    (1, 0, 2, 5), (-1, 0, 2, 5), (0, 1, 2, 5), (0, -1, 2, 5),

                    # Three-axis combinations
                    (1, 1, 1, 5), (1, -1, 1, 5), (-1, 1, 1, 5), (-1, -1, 1, 5)
                    ]:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if 0 <= nx < self.n and 0 <= ny < self.m and 0 <= nz < self.height:
                        self.grid_values[(nx, ny, nz)] = cost

            # If node used >=3 times, apply smaller ring
            elif node_counts[node] >= 3 or (node_counts[node] >= 2 and self.count_neighbors(x,y,z) <= 3):
                for dx, dy, dz, cost in [
                    (0, 0, 1, 40),  # Above
                    (0, -1, 0, 40), (0, 1, 0, 40),  # Vertical neighbors
                    (-1, 0, 0, 40), (1, 0, 0, 40),  # Horizontal neighbors

                    (0, 0, 2, 20),  # Two steps above
                    (0, -2, 0, 20), (0, 2, 0, 20),  # Two steps vertical
                    (-2, 0, 0, 20), (2, 0, 0, 20),  # Two steps horizontal
                    (-1, -1, 0, 20), (-1, 1, 0, 20), (1, 1, 0, 20), (1, -1, 0, 20), # Non direct neighbors bottom layer
                    (1, 0, 1, 20), (-1, 0, 1, 20), (0, -1, 1, 25), (0, 1, 1, 25) # One horizontal one vertical
                ]:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if 0 <= nx < self.n and 0 <= ny < self.m and 0 <= nz < self.height:
                        self.grid_values[(nx, ny, nz)] = cost

        # If node used >=2 times, apply a small ring
            elif node_counts[node] >= 2:
                for dx, dy, dz, cost in [
                    (0, 0, 1, 30),  # Above
                    (0, -1, 0, 30), (0, 1, 0, 30),  # Vertical neighbors
                    (-1, 0, 0, 30), (1, 0, 0, 30)  # Horizontal neighbors
                ]:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if 0 <= nx < self.n and 0 <= ny < self.m and 0 <= nz < self.height:
                        self.grid_values[(nx, ny, nz)] = cost


        # -----------------------------------------------------
        # 2) MAKE OUTER CELLS CHEAPER AND CENTER CELLS PRICIER
        # -----------------------------------------------------
        #
        # We'll do a simple formula: the cost at each cell (x,y,z)
        # will be increased by an amount proportional to "distance from the edge."
        #
        # distance_to_edge = min(x, (self.n - 1 - x), y, (self.m - 1 - y), z, (self.height - 1 - z))
        #
        # The bigger that distance, the more "center" the cell is => the bigger cost we add.

        for x in range(self.n):
            for y in range(self.m):
                for z in range(self.height):
                    dist_to_edge = min(
                        x,               # distance from left edge
                        self.n - 1 - x,  # distance from right edge
                        y,               # distance from top edge
                        self.m - 1 - y,  # distance from bottom edge
                        z,               # distance from top layer in 3D
                        self.height - 1 - z  # distance from bottom layer in 3D
                    )

                    cost_bump = dist_to_edge * 2

                    self.grid_values[(x, y, z)] += cost_bump



    def clear_wires(self):
        """
        Deletes all wires from wire. 
        """
        self._wires = []
        self._lines_count = 0
        self._wires_segments = set()
        self._reserved_points = set()
        self.failed_wires = 0
        self.total_wires = 0
        self._point_dict = {
            (x, y, z): 0
            for x in range(self.n)
            for y in range(self.m)
            for z in range(self.height)
        }
        self.grid_values = {
            (x, y, z): 1 for x in range(self.n) for y in range(self.m) for z in range(self.height)
        }

    def remove_wire(self, wire: Wire) -> None:
        """
        Removes a wire from the grid and updates the grid's data structures.

        Args:
            wire (Wire): The wire to remove.
        """
        # Get the wirepoints from the wire
        wirepoints = wire.give_wirepoints()

        # Iterate through the wirepoints and update the grid values and point dictionary
        for point in wirepoints:
            x, y, z = point.give_x(), point.give_y(), point.give_z()

            # Update the grid values to default (1 in this case)
            self.grid_values[(x, y, z)] = 1

            # Decrease the count in the point dictionary
            if (x, y, z) in self._point_dict:
                self._point_dict[(x, y, z)] -= 1
                if self._point_dict[(x, y, z)] < 0:
                    self._point_dict[(x, y, z)] = 0

        # Remove segments associated with the wire from the segment set
        for i in range(len(wirepoints) - 1):
            start_point = wirepoints[i]
            end_point = wirepoints[i + 1]
            segment = Segment(start_point, end_point)
            if segment in self._wires_segments:
                self._wires_segments.remove(segment)

        # Remove the wire from the list of wires
        if wire in self._wires:
            self._wires.remove(wire)

        # Update line count
        self._lines_count -= len(wirepoints) - 1
        if self._lines_count < 0:
            self._lines_count = 0


    def give_height(self) -> int:
        """
        Returns the height of the grid.
        """
        return self.n
    

    def give_width(self) -> int:
        """
        Returns the width of the grid.
        """
        return self.m


    def place_node(self, node: Node, z=0) -> None:
        """
        Places a node at the baselayer level at given coordinates.
        """
        if not (0 <= node.give_x() <= self.n and 0 <= node.give_y() <= self.m and 0 <= z < self.height):
            raise IndexError("Coördinaten buiten de grid.")
        
    
    def add_wire_list(self, wire) -> None:
        """
        Add a wire to the list of wires
        """
        self._wires.append(wire)


    def return_wire_list(self) -> list[Wire]:
        """
        Returns the list of wires
        """
        return self._wires


    def add_wire_dict(self, wire) -> None:
        """
        Adds a wire to the wirepoint dictionary and updates the segment set.
        """
        from code.classes.wire_class import WirePoint

        wirepoints = wire.give_wirepoints()
        for i in range(len(wirepoints) - 1):
            start_point = wirepoints[i]
            end_point = wirepoints[i + 1]

            x, y, z = start_point.give_x(), start_point.give_y(), start_point.give_z()
            if 0 <= x < self.n and 0 <= y < self.m and 0 <= z < self.height:
                self._point_dict[(x, y, z)] += 1
            else:
                raise IndexError("Coordinates outside the grid.")
        
        self._lines_count += len(wirepoints) - 1


    def add_wire_segment(self, segment: Segment) -> None:
        """
        Adds a segment to the set of segments.
        """
        self._wires_segments.add(segment)

    
    def add_entire_wire_segments(self, wire: Wire) -> None:
        """
        Adds the entire segment set of a wire to the grid. 
        """
        segments = wire.give_segments()
        self._wires_segments.update(segments)


    def remove_nodes_pointdict(self):
        """
        Removes the nodes from the point dictionary, to make sure they don't count as intersections
        """
        for node in self._nodes:
            self._point_dict[(node.give_x(), node.give_y(), 0)] = 0


    def distance_nodes(self, node1: Node, node2: Node) -> int:
        """
        Returns the manhattan distance between two nodes.
        """
        return (abs(node1.give_x() - node2.give_x()) +
            abs(node1.give_y() - node2.give_y()) +
            abs(node1.give_z() - node2.give_z()))



    def check_wire_overlap(self, current_wire) -> bool:
        """
        Checks if the wire does not run over another wire in any direction.
        Uses the precomputed set of segments for efficient checks.
        """
        if len(self._wires_segments) == 0:
            return True
        
        current_segment = Segment(current_wire.give_wirepoints()[-3], current_wire.give_wirepoints()[-2])

        if current_segment in self._wires_segments:
            return False
            
        return True
    
    def add_reservation(self, point: WirePoint) -> None:
        """
        Adds the given point to reserved points, as well as the neighboring points
        (x-1, x+1, y-1, y+1, and z+1).
        """

        # Extract coordinates
        x, y, z = point.give_x(), point.give_y(), point.give_z()

        # Add the neighboring points
        self._reserved_points.add(WirePoint(x - 1, y, z))
        self._reserved_points.add(WirePoint(x + 1, y, z))
        self._reserved_points.add(WirePoint(x, y - 1, z))
        self._reserved_points.add(WirePoint(x, y + 1, z))
        self._reserved_points.add(WirePoint(x, y, z + 1))
    

    def check_reservation(self, point: WirePoint) -> bool:
        """
        Checks if a wire does not go over a reserved point
        """
        if (WirePoint(point.give_x(), point.give_y(), point.give_z())) in self._reserved_points:
            return False
        
        return True
    

    def check_not_through_node(self, point: WirePoint) -> bool:
        """
        Checks if a wirepoint doesn't have the same coordinates as a node
        """
        for node in self._nodes:
            if (point.give_x(), point.give_y(), point.give_z()) == (node.give_x(), node.give_y(), node.give_z()):
                return False

        return True    

    def check_obstacle(self, point: WirePoint, segment: Segment) -> bool:
        """
        Checks if a wirepoint does not collide with an obstacle.
        """
        
        if not self.check_in_grid(point):
            return False
        
        if not self.check_not_through_node(point):
            return False
        
        if not self.check_wire_overlap_point(segment):
            return False
        
        return True
        

    def check_wire_overlap_point(self, segment: Segment) -> bool:  
        """
        Checks if the wire does not run over another wire in any direction.
        Uses the precomputed set of segments for efficient checks.
        """
        if segment in self._wires_segments:
            return False
            
        return True

    def check_in_grid(self, point: WirePoint) -> bool:
        """
        Checks if a given point exists in the grid
        """
        wire_point = point
        if (wire_point.give_x(), wire_point.give_y(), wire_point.give_z()) not in self._point_dict:
            return False
        
        return True


    def check_valid_addition(self, current_wire: Wire) -> bool:
        """
        Checks if the last point in the current wire wirepoints list does not overwrite any rules.
        """
        from code.classes.wire_class import WirePoint, Wire

        # Ensure the wire has at least two points
        if len(current_wire.give_wirepoints()) < 2:
            return False

        #Checks if the wirepoint is in the grid.
        wire_point = current_wire.give_wirepoints()[-2]
        if (wire_point.give_x(), wire_point.give_y(), wire_point.give_z()) not in self._point_dict:
            return False

        #Checks if the wirepoint does not run over another wire.
        if not self.check_wire_overlap(current_wire):
            return False
                
        #Checks if the wirepoint does not go through node.
        if not current_wire.check_not_through_node():
            return False
        
        #Checks if the wire does not return on itself
        #if not current_wire.check_not_return():
        #    print("Would return on itself")
        #    return False
        
        #if not self.check_reservation(wire_point):
        #    return False

        return True


    def total_intersections(self) -> int:
        """
        Calculates the total intersections based on if the value of the point dict is larger than 1.
        """
        self.remove_nodes_pointdict()
        intersections = 0
        for value in self._point_dict.values():
            if value > 1:
                intersections += (value - 1)
        return intersections
    

    def give_nodes(self) -> list[Node]:
        """
        Returns the list of nodes.
        """
        return self._nodes


    def cost(self) -> int:
        """
        Calculates the total cost:
        - 300 per intersection
        - 1 per line
        """
        intersections = self.total_intersections()
        return intersections * 300 + self._lines_count
    

    def cost_point(self, point: WirePoint) -> int:
        """
        Calculates the cost of a given point.
        """
        if self._point_dict[point.give_place()] > 1:
            return self._point_dict[point.give_place()] * 300 + 1
        
        else:
            return 1
        
        
def initialise_grid(nodes_list, nodes_csv_path):
    grid_width = max(node._max_value for node in nodes_list) + 1
    grid_length = max(node._max_value for node in nodes_list) + 1
    grid = Grid_3D(grid_width, grid_length, nodes_csv_path)
    for node in nodes_list:
        grid.place_node(node)
    return grid, grid_width, grid_length
   
def plot_wires_3d(wires: list[Wire], grid_width: int, grid_height: int):
    """
    A function used to plot the wires of the grid in 3D.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for wire in wires:
        xs = [p.give_x() for p in wire.give_wirepoints()]
        ys = [p.give_y() for p in wire.give_wirepoints()]
        zs = [p.give_z() for p in wire.give_wirepoints()]
        
        # Teken de lijnen langs de wirepoints
        ax.plot(xs, ys, zs, marker='o')

    ax.set_xlim(0, grid_width)
    ax.set_ylim(0, grid_height)
    ax.set_zlim(0, 7)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()