import numpy as np
from nodes_class import Node
from nodes_class import importeer_nodes

class WirePoint:
    """
    Representatie van één coördinaat in een 3D-grid,
    gebruikt in de Wire-class om een draad (wire) op te bouwen.
    """
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def give_place(self):
        """Retourneert (x, y, z)."""
        return (self.x, self.y, self.z)
    
    def give_x(self) -> int:
        return self.x
    
    def give_y(self) -> int:
        return self.y
    
    def give_z(self) -> int:
        return self.z
        
class Wire:
    """Connecteert WirePoints aaneen tot een draad in 3D."""
    
    def __init__(self, wirepoints: list[WirePoint]) -> None:
        self.wirepoints = wirepoints
        self.nodes = importeer_nodes('../gates&netlists/chip_0/print_0.csv')

    def check_wire(self) -> bool:
        """Checkt of deze wire in 3D netjes aaneengesloten is (1 stap per keer in x/y/z)."""
        for i in range(len(self.wirepoints) - 1):
            current = self.wirepoints[i]
            next_point = self.wirepoints[i + 1]
            
            if not (
                # x verschilt met 1
                (abs(current.give_x() - next_point.give_x()) == 1 and
                 current.give_y() == next_point.give_y() and
                 current.give_z() == next_point.give_z()) or
                # y verschilt met 1
                (abs(current.give_y() - next_point.give_y()) == 1 and
                 current.give_x() == next_point.give_x() and
                 current.give_z() == next_point.give_z()) or
                # z verschilt met 1
                (abs(current.give_z() - next_point.give_z()) == 1 and
                 current.give_x() == next_point.give_x() and
                 current.give_y() == next_point.give_y())
            ):
                return False
        return True

    def check_connection(self, node1: Node, node2: Node) -> bool:
        """
        Checkt of de wire inderdaad begint bij (node1.x, node1.y)
        en eindigt bij (node2.x, node2.y), of andersom.
        """
        first_wp = self.wirepoints[0]
        last_wp = self.wirepoints[-1]
        return (
            ((first_wp.x, first_wp.y) == (node1.x, node1.y) and
             (last_wp.x, last_wp.y) == (node2.x, node2.y))
            or
            ((first_wp.x, first_wp.y) == (node2.x, node2.y) and
             (last_wp.x, last_wp.y) == (node1.x, node1.y))
        )
    
    def check_not_through_node(self) -> bool:
        """
        Checkt of een wire niet door een node heen gaat. 
        """
        for x in range(len(self.wirepoints)):
            if self.wirepoints[x].z != 0:
                return True
            
            if x == 0 or x == len(self.wirepoints) - 1:
                continue
            else:
                for n in self.nodes:
                    if (self.wirepoints[x].x, self.wirepoints[x].y) == (n.x, n.y):
                        return False
        return True
