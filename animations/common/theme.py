# animations/common/theme.py
"""Shared visual theme for nanoNova animations.

Hybrid style: 3B1B dark background with diagram overlay labels.
"""

from manim import (
    BLUE_C,
    GREEN_C,
    RED_C,
    YELLOW_C,
    WHITE,
    GREY_B,
    GREY_D,
)

# === Colors ===
# Matrix colors (R1CS)
MATRIX_A_COLOR = BLUE_C
MATRIX_B_COLOR = GREEN_C
MATRIX_C_COLOR = RED_C
VECTOR_Z_COLOR = YELLOW_C
WITNESS_COLOR = "#fcba03"

# Instance colors (Folding)
INSTANCE_1_COLOR = BLUE_C
INSTANCE_2_COLOR = GREEN_C
FOLDED_COLOR = "#bb86fc"  # Purple
CROSS_TERM_COLOR = "#ff6b6b"

# IVC colors
ACCUMULATOR_COLOR = "#bb86fc"
FRESH_INSTANCE_COLOR = YELLOW_C
CHECKMARK_COLOR = GREEN_C

# General
LABEL_COLOR = GREY_B
DIM_COLOR = GREY_D
HIGHLIGHT_COLOR = WHITE

# === Animation Timing ===
FAST = 0.3
NORMAL = 0.6
SLOW = 1.0
VERY_SLOW = 1.5

# === Font Sizes ===
TITLE_SIZE = 48
HEADING_SIZE = 36
BODY_SIZE = 28
LABEL_SIZE = 22
SMALL_SIZE = 18

# === Layout ===
MATRIX_CELL_SIZE = 0.5
VECTOR_CELL_SIZE = 0.5
INSTANCE_BOX_WIDTH = 2.5
INSTANCE_BOX_HEIGHT = 1.8
