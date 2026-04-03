"""Animation 1: What is R1CS?

NARRATION OVERVIEW:
A computation is a set of constraints. We encode them as matrices.
R1CS lets us prove we know a solution without revealing it.
Then we "relax" the system to enable something powerful: folding.

DURATION: ~5 minutes total
CLIPS FOR ZKPROOF 8: Scenes 1.2 (R1CS equation) and 1.4 (relaxation)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from manim import (
    Scene,
    Text,
    MathTex,
    VGroup,
    FadeIn,
    FadeOut,
    Write,
    TransformMatchingTex,
    LEFT,
    RIGHT,
    UP,
    DOWN,
    WHITE,
    GREY_B,
)
from common.theme import (
    TITLE_SIZE,
    HEADING_SIZE,
    BODY_SIZE,
    SMALL_SIZE,
    SLOW,
    NORMAL,
    VERY_SLOW,
    MATRIX_A_COLOR,
    MATRIX_B_COLOR,
    MATRIX_C_COLOR,
    VECTOR_Z_COLOR,
    WITNESS_COLOR,
    FOLDED_COLOR,
    CROSS_TERM_COLOR,
)
from common.components import MatrixGrid, VectorStack


class R1CSIntro(Scene):
    """Scene 1.1: A computation is a set of constraints.

    NARRATION:
    "Every computation can be expressed as a set of constraints.
     Take a simple example: we know three numbers a, b, and c,
     and we claim that a + b = c.
     A verifier could check this directly — but what if there
     are thousands of constraints? What if we don't want to
     reveal a, b, or c?
     We need a better encoding. Enter: R1CS."

    DURATION: ~30 seconds
    """

    def construct(self):
        title = Text("What is R1CS?", font_size=TITLE_SIZE, color=WHITE)
        subtitle = Text("Rank-1 Constraint System", font_size=HEADING_SIZE, color=GREY_B)
        subtitle.next_to(title, DOWN, buff=0.3)
        self.play(Write(title), run_time=SLOW)
        self.play(FadeIn(subtitle), run_time=NORMAL)
        self.wait(1)

        self.play(FadeOut(title), FadeOut(subtitle))
        eq = MathTex("a + b = c", font_size=TITLE_SIZE, color=WITNESS_COLOR)
        self.play(Write(eq), run_time=SLOW)
        self.wait(1)

        question = Text(
            "What if there are thousands of these?",
            font_size=BODY_SIZE,
            color=GREY_B,
        )
        question.next_to(eq, DOWN, buff=0.5)
        self.play(FadeIn(question), run_time=NORMAL)
        self.wait(1)

        self.play(FadeOut(eq), FadeOut(question))
        answer = Text("We encode them as matrix equations.", font_size=BODY_SIZE, color=WHITE)
        self.play(Write(answer), run_time=NORMAL)
        self.wait(1)
        self.play(FadeOut(answer))


class R1CSEquation(Scene):
    """Scene 1.2: Az ∘ Bz = Cz animated.

    NARRATION:
    "R1CS encodes constraints using three matrices: A, B, and C.
     Given a vector z containing our inputs and witness,
     we compute A times z, B times z, and C times z.
     The constraint is satisfied when the element-wise product
     of Az and Bz equals Cz.
     That dot in the middle? It's the Hadamard product —
     multiply corresponding elements, not a dot product."

    DURATION: ~90 seconds
    CLIP: ZKProof talk — core R1CS visual
    """

    def construct(self):
        eq1 = MathTex("A", r"\vec{z}", color=MATRIX_A_COLOR, font_size=HEADING_SIZE)
        eq1.move_to(LEFT * 3.5)
        self.play(Write(eq1), run_time=NORMAL)

        dot = MathTex(r"\circ", font_size=HEADING_SIZE, color=WHITE)
        dot.next_to(eq1, RIGHT, buff=0.3)

        eq2 = MathTex("B", r"\vec{z}", color=MATRIX_B_COLOR, font_size=HEADING_SIZE)
        eq2.next_to(dot, RIGHT, buff=0.3)
        self.play(Write(dot), Write(eq2), run_time=NORMAL)

        equals = MathTex("=", font_size=HEADING_SIZE, color=WHITE)
        equals.next_to(eq2, RIGHT, buff=0.3)

        eq3 = MathTex("C", r"\vec{z}", color=MATRIX_C_COLOR, font_size=HEADING_SIZE)
        eq3.next_to(equals, RIGHT, buff=0.3)
        self.play(Write(equals), Write(eq3), run_time=NORMAL)
        self.wait(1)

        full_eq = VGroup(eq1, dot, eq2, equals, eq3)
        self.play(full_eq.animate.to_edge(UP, buff=0.5).scale(0.7), run_time=NORMAL)

        A_vals = [[1, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]]
        B_vals = [[0, 1, 1, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1]]
        C_vals = [[0, 0, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0]]

        A_grid = MatrixGrid(A_vals, color=MATRIX_A_COLOR, label="A")
        B_grid = MatrixGrid(B_vals, color=MATRIX_B_COLOR, label="B")
        C_grid = MatrixGrid(C_vals, color=MATRIX_C_COLOR, label="C")

        A_grid.scale(0.6).move_to(LEFT * 4 + DOWN * 0.5)
        B_grid.scale(0.6).move_to(DOWN * 0.5)
        C_grid.scale(0.6).move_to(RIGHT * 4 + DOWN * 0.5)

        self.play(FadeIn(A_grid), FadeIn(B_grid), FadeIn(C_grid), run_time=SLOW)
        self.wait(1)

        z = VectorStack([1, 1, 1, 1, 2, 2], color=VECTOR_Z_COLOR, label="z")
        z.scale(0.5).move_to(DOWN * 3)
        z_label = Text(
            "z = (1, a, b, b, a+b, w)",
            font_size=SMALL_SIZE,
            color=VECTOR_Z_COLOR,
        )
        z_label.next_to(z, DOWN, buff=0.2)
        self.play(FadeIn(z), FadeIn(z_label), run_time=NORMAL)
        self.wait(2)

        self.play(
            FadeOut(A_grid),
            FadeOut(B_grid),
            FadeOut(C_grid),
            FadeOut(z),
            FadeOut(z_label),
            FadeOut(full_eq),
        )


class R1CSRelaxation(Scene):
    """Scene 1.4: Introducing Relaxed R1CS.

    NARRATION:
    "Standard R1CS works for one computation.
     But what if we want to COMBINE two valid computations?
     We need to 'relax' the system.
     Instead of Az times Bz equals Cz,
     we introduce a scalar u and an error vector E:
     Az times Bz equals u times Cz, plus E.
     When u is 1 and E is zero, this is just regular R1CS.
     But when we fold two instances together,
     u and E absorb the cross-terms.
     This is the key insight of Nova."

    DURATION: ~60 seconds
    CLIP: ZKProof talk — motivation for relaxation
    """

    def construct(self):
        standard = MathTex(
            r"A\vec{z}",
            r"\circ",
            r"B\vec{z}",
            "=",
            r"C\vec{z}",
            font_size=HEADING_SIZE,
        )
        standard[0].set_color(MATRIX_A_COLOR)
        standard[2].set_color(MATRIX_B_COLOR)
        standard[4].set_color(MATRIX_C_COLOR)
        self.play(Write(standard), run_time=SLOW)
        self.wait(1)

        q = Text("Can we combine two of these?", font_size=BODY_SIZE, color=GREY_B)
        q.next_to(standard, DOWN, buff=0.5)
        self.play(FadeIn(q), run_time=NORMAL)
        self.wait(1)
        self.play(FadeOut(q))

        relaxed = MathTex(
            r"A\vec{z}",
            r"\circ",
            r"B\vec{z}",
            "=",
            "u",
            r"\cdot",
            r"C\vec{z}",
            "+",
            r"\vec{E}",
            font_size=HEADING_SIZE,
        )
        relaxed[0].set_color(MATRIX_A_COLOR)
        relaxed[2].set_color(MATRIX_B_COLOR)
        relaxed[4].set_color(FOLDED_COLOR)
        relaxed[6].set_color(MATRIX_C_COLOR)
        relaxed[8].set_color(CROSS_TERM_COLOR)
        self.play(TransformMatchingTex(standard, relaxed), run_time=VERY_SLOW)
        self.wait(1)

        u_note = Text("u = 1 for real instances", font_size=SMALL_SIZE, color=FOLDED_COLOR)
        e_note = Text("E = 0 for real instances", font_size=SMALL_SIZE, color=CROSS_TERM_COLOR)
        u_note.next_to(relaxed, DOWN, buff=0.5)
        e_note.next_to(u_note, DOWN, buff=0.2)
        self.play(FadeIn(u_note), FadeIn(e_note), run_time=NORMAL)
        self.wait(1)

        tease = Text(
            "When u \u2260 1 and E \u2260 0... folding happens.",
            font_size=BODY_SIZE,
            color=WHITE,
        )
        self.play(FadeOut(u_note), FadeOut(e_note))
        tease.next_to(relaxed, DOWN, buff=0.5)
        self.play(Write(tease), run_time=SLOW)
        self.wait(2)

        self.play(FadeOut(relaxed), FadeOut(tease))
