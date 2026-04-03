"""Quick preview of shared components. Not a real animation — just for visual testing."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from manim import Scene, FadeIn, LEFT, RIGHT, UP, DOWN
from common.theme import MATRIX_A_COLOR, VECTOR_Z_COLOR, INSTANCE_1_COLOR, INSTANCE_2_COLOR
from common.components import MatrixGrid, VectorStack, InstanceBox


class ComponentPreview(Scene):
    def construct(self):
        # Matrix A
        A = MatrixGrid(
            [[1, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]],
            color=MATRIX_A_COLOR,
            label="A",
        )
        A.scale(0.8).to_edge(LEFT, buff=0.5).shift(UP)
        self.play(FadeIn(A))
        self.wait(0.5)

        # Vector z
        z = VectorStack([1, 1, 1, 1, 2, 2], color=VECTOR_Z_COLOR, label="z")
        z.scale(0.8).next_to(A, RIGHT, buff=1)
        self.play(FadeIn(z))
        self.wait(0.5)

        # Instance boxes
        box1 = InstanceBox("Instance\u2081", color=INSTANCE_1_COLOR, u_val="1")
        box2 = InstanceBox("Instance\u2082", color=INSTANCE_2_COLOR, u_val="1")
        box1.shift(DOWN * 2 + LEFT * 2)
        box2.shift(DOWN * 2 + RIGHT * 2)
        self.play(FadeIn(box1), FadeIn(box2))
        self.wait(1)
