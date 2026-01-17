#!/usr/bin/env python3

TRANSITIONS = {}
for i in range(1, 1001):
    base = i % 7
    # Use prime numbers or larger ranges to prevent patterns from repeating
    if base == 0: 
        TRANSITIONS[i] = ["out-l", "in-l", i] # Each ID has a unique pixel offset
    elif base == 1: 
        TRANSITIONS[i] = ["out-r", "in-r", i]
    elif base == 2: 
        TRANSITIONS[i] = ["out-u", "in-u", i]
    elif base == 3: 
        TRANSITIONS[i] = ["out-d", "in-d", i]
    elif base == 4: 
        # Spins from 90 to 1090 degrees
        deg = 90 + i 
        TRANSITIONS[i] = ["out-rot", "in-rot", deg]
    elif base == 5:
        deg = 90 + i
        TRANSITIONS[i] = ["out-rot", "in-rot", -deg]
    elif base == 6:
        # Zoom scale from 1.01x to 11.0x
        depth = 1 + (i / 100.0)
        TRANSITIONS[i] = ["out-zoom", "in-zoom", depth]

groups = {}
for tid, data in TRANSITIONS.items():
    logic_signature = tuple(data) 
    if logic_signature not in groups:
        groups[logic_signature] = []
    groups[logic_signature].append(tid)

print(f"Total Unique Behaviors Found: {len(groups)} / 1000")
