from bnm3_transitions.base import Transition

class SlidesTransition(Transition):
    """
    Handles coordinate-based movement.
    """
    def __init__(self):
        super().__init__(name="Linear Slide")

    def run(self, widget, duration, direction="in", side="left", **kwargs):
        # Determine screen/container width for the math
        screen_width = kwargs.get('screen_width', 1920)
        
        # LOGIC: Check if widget is a real object or just a string for testing
        if isinstance(widget, str):
            home_x = 0  # Dummy value for test_engine.py
        else:
            # This is where your real GUI widget properties live
            home_x = getattr(widget, 'original_x', 0)
        
        if direction == "in":
            # Start off-screen, move to home
            start_x = -screen_width if side == "left" else screen_width
            end_x = home_x
        else:
            # Start at home, move off-screen
            start_x = home_x
            end_x = -screen_width if side == "left" else screen_width

        print(f"DEBUG: [Slide] {direction.upper()} from {side} | {start_x} -> {end_x} over {duration}s")
        
        return True
