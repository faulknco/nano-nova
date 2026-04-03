# animations/common/components.py
"""Reusable Manim components for nanoNova animations."""

from manim import (
    VGroup,
    Square,
    Text,
    MathTex,
    RoundedRectangle,
    DOWN,
    UP,
    ORIGIN,
    WHITE,
    GREY_D,
)
from .theme import (
    MATRIX_CELL_SIZE,
    VECTOR_CELL_SIZE,
    LABEL_SIZE,
    SMALL_SIZE,
)


class MatrixGrid(VGroup):
    """Animated matrix display with colored cells.

    Usage:
        m = MatrixGrid([[1,0,0],[0,1,0]], color=BLUE_C, label="A")
        self.play(FadeIn(m))
        m.highlight_cell(0, 1, color=YELLOW)
    """

    def __init__(self, values, color, label=None, cell_size=MATRIX_CELL_SIZE, **kwargs):
        super().__init__(**kwargs)
        self.values = values
        self.rows = len(values)
        self.cols = len(values[0]) if values else 0
        self.cell_size = cell_size
        self.cells = []
        self.texts = []

        for i, row in enumerate(values):
            cell_row = []
            text_row = []
            for j, val in enumerate(row):
                cell = Square(side_length=cell_size)
                cell.set_stroke(color, width=1.5)
                cell.set_fill(color, opacity=0.15 if val != 0 else 0.02)
                cell.move_to([j * cell_size, -i * cell_size, 0])
                self.add(cell)
                cell_row.append(cell)

                txt = Text(str(val), font_size=SMALL_SIZE, color=WHITE)
                txt.move_to(cell.get_center())
                self.add(txt)
                text_row.append(txt)

            self.cells.append(cell_row)
            self.texts.append(text_row)

        self.move_to(ORIGIN)

        if label:
            self.label = MathTex(label, font_size=LABEL_SIZE, color=color)
            self.label.next_to(self, UP, buff=0.2)
            self.add(self.label)

    def highlight_row(self, row_idx, color, opacity=0.5):
        """Return animations to highlight a row."""
        return [cell.animate.set_fill(color, opacity=opacity) for cell in self.cells[row_idx]]

    def highlight_cell(self, row, col, color, opacity=0.6):
        """Return animation to highlight a single cell."""
        return self.cells[row][col].animate.set_fill(color, opacity=opacity)


class VectorStack(VGroup):
    """Vertical vector display with number labels.

    Usage:
        v = VectorStack([1, 2, 3], color=YELLOW_C, label="z")
        self.play(FadeIn(v))
    """

    def __init__(self, values, color, label=None, cell_size=VECTOR_CELL_SIZE, **kwargs):
        super().__init__(**kwargs)
        self.values = values
        self.cell_size = cell_size
        self.cells = []
        self.texts = []

        for i, val in enumerate(values):
            cell = Square(side_length=cell_size)
            cell.set_stroke(color, width=1.5)
            cell.set_fill(color, opacity=0.15)
            cell.move_to([0, -i * cell_size, 0])
            self.add(cell)
            self.cells.append(cell)

            txt = Text(str(val), font_size=SMALL_SIZE, color=WHITE)
            txt.move_to(cell.get_center())
            self.add(txt)
            self.texts.append(txt)

        self.move_to(ORIGIN)

        if label:
            self.label = MathTex(label, font_size=LABEL_SIZE, color=color)
            self.label.next_to(self, UP, buff=0.2)
            self.add(self.label)

    def highlight_element(self, idx, color, opacity=0.5):
        """Return animation to highlight one element."""
        return self.cells[idx].animate.set_fill(color, opacity=opacity)


class InstanceBox(VGroup):
    """Labeled box representing a Relaxed R1CS instance.

    Shows: label, u value, and a colored border.

    Usage:
        box = InstanceBox("Instance₁", color=BLUE_C, u_val="1")
        self.play(FadeIn(box))
    """

    def __init__(self, label_text, color, u_val=None, width=2.5, height=1.5, **kwargs):
        super().__init__(**kwargs)

        self.box = RoundedRectangle(
            corner_radius=0.15,
            width=width,
            height=height,
        )
        self.box.set_stroke(color, width=2)
        self.box.set_fill(color, opacity=0.1)
        self.add(self.box)

        self.title = Text(label_text, font_size=LABEL_SIZE, color=color)
        self.title.move_to(self.box.get_top() + DOWN * 0.3)
        self.add(self.title)

        if u_val is not None:
            self.u_text = MathTex(f"u={u_val}", font_size=SMALL_SIZE, color=GREY_D)
            self.u_text.move_to(self.box.get_center())
            self.add(self.u_text)

    def get_box(self):
        return self.box
