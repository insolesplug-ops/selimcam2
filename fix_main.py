#!/usr/bin/env python3
"""Fix the _rotate_touch function in main.py"""

with open('main.py', 'r') as f:
    content = f.read()

# Replace the entire problematic section
old_section = """    # -------- TOUCH COORDINATE MAPPING (PORTRAIT) --------
    def _rotate_touch(self, px: int, py: int) -> tuple:
        \"\"\"
        Physical landscape coordinates -> logical portrait coordinates.
        180-degree flip mapping (from user spec):
            x_mapped = LOGICAL_W - x_raw
            y_mapped = LOGICAL_H - y_raw
        \"\"\"
        lx = int(LOGICAL_W - px)
        ly = int(LOGICAL_H - py)
        # Clamp
        lx = max(0, min(LOGICAL_W - 1, lx))
        ly = max(0, min(LOGICAL_H - 1, ly))
        return (lx, ly)"""

new_section = """    def _rotate_touch(self, px: int, py: int) -> tuple:
        \"\"\"180 degree flip: x_mapped = 480 - x_raw, y_mapped = 800 - y_raw\"\"\"
        lx = max(0, min(479, int(480 - px)))
        ly = max(0, min(799, int(800 - py)))
        return (lx, ly)"""

if old_section in content:
    content = content.replace(old_section, new_section)
    with open('main.py', 'w') as f:
        f.write(content)
    print("✓ Fixed")
else:
    print("Could not find the old section")
    # Try searching for the function any way
    if 'def _rotate_touch' in content:
        print("Function exists, trying alternate method...")
