import time
from bnm3_transitions.base import Transition

class WipesTransition(Transition):
    def __init__(self):
        super().__init__(name="Geometric Wipe")

    def run(self, widget, duration, direction="in", pattern="linear", **kwargs):
        steps = 20
        sleep_time = duration / steps
        
        # In: 0% visibility -> 100% visibility
        # Out: 100% visibility -> 0% visibility
        current_mask = 0 if direction == "in" else 100
        target_mask = 100 if direction == "in" else 0
        step_size = (target_mask - current_mask) / steps

        print(f"DEBUG: Starting {pattern.upper()} Wipe {direction.upper()}...")

        for i in range(steps):
            current_mask += step_size
            
            if hasattr(widget, 'set_mask_percentage'):
                widget.set_mask_percentage(current_mask)
            else:
                if i % 5 == 0:
                    print(f"  [Step {i}] Mask Coverage: {int(current_mask)}%")
            
            time.sleep(sleep_time)

        print(f"DEBUG: Wipe {direction.upper()} Complete.")
        return True
