import numpy as np

class WirePoint:
    """Deze class zijn 3 coordinaten die de wire class gebruikt om een draad te vormen"""

    def __init__ (self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def give_place(self):
        """Gives back the coordinates of the current wire section"""
        return (self.x, self.y, self.z)
    
    def give_x(self) -> int:
        return self.x
    
    def give_y(self) -> int:
        return self.y
    
    def give_z(self) -> int:
        return self.z

class Wire:
    """Connect de wire points met elkaar om tot een wire te komen"""
    def __init__(self, wirepoints: list[WirePoint]) -> None:
        self.wirepoints = wirepoints

    def check_connection(self) -> bool:
        """Checkt of een draad goed verbonden is"""
        for i in range(len(self.wirepoints) - 1):
            current = self.wirepoints[i]
            next_point = self.wirepoints[i + 1]
            
            if not ((np.abs(current.give_x() - next_point.give_x()) == 1 and 
                     current.give_y() == next_point.give_y() and 
                     current.give_z() == next_point.give_z()) or
                    (np.abs(current.give_y() - next_point.give_y()) == 1 and 
                     current.give_x() == next_point.give_x() and 
                     current.give_z() == next_point.give_z()) or
                    (np.abs(current.give_z() - next_point.give_z()) == 1 and 
                     current.give_x() == next_point.give_x() and 
                     current.give_y() == next_point.give_y())):
                return False
        
        return True
