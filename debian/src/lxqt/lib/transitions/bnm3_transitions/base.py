from abc import ABC, abstractmethod

class Transition(ABC):
    """
    The Base Transition Class. 
    Every transition category MUST inherit from this to ensure 
    orthogonality and consistent behavior.
    """
    def __init__(self, name, version="1.0.0"):
        self.name = name
        self.version = version

    @abstractmethod
    def run(self, widget, duration, direction="in", **kwargs):
        """
        The main execution method.
        :param widget: The UI element to animate.
        :param duration: Time in seconds.
        :param direction: 'in' or 'out' to handle symmetry.
        """
        pass
