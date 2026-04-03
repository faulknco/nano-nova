"""Animation 2: Nova Folding — Two Become One.

NARRATION OVERVIEW:
Two valid constraint instances. Can we combine them into one?
The cross-term T absorbs the interference from quadratic constraints.
A Fiat-Shamir challenge provides verifier randomness without a verifier.
The fold merges everything: E, u, x, W — same size output as input.

DURATION: ~6 minutes total
CLIPS FOR ZKPROOF 8: Scene 2.5 (the fold animation)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from manim import (
    Scene,
    Text,
    MathTex,
    VGroup,
    Arrow,
    FadeIn,
    FadeOut,
    Write,
    Create,
    Flash,
    LEFT,
    RIGHT,
    UP,
    DOWN,
    ORIGIN,
    WHITE,
    GREY_B,
)
from common.theme import (
    BODY_SIZE,
    LABEL_SIZE,
    SMALL_SIZE,
    TITLE_SIZE,
    SLOW,
    NORMAL,
    FAST,
    INSTANCE_1_COLOR,
    INSTANCE_2_COLOR,
    FOLDED_COLOR,
    CROSS_TERM_COLOR,
    WITNESS_COLOR,
)
from common.components import InstanceBox


class FoldingSetup(Scene):
    """Scene 2.2-2.3: Two instances + cross-term.

    NARRATION:
    "We have two valid relaxed R1CS instances.
     Each has its own u, E, x, and W.
     Can we combine them into a single instance?
     The problem: R1CS is quadratic. When we add two quadratic
     expressions, cross-terms appear.
     T absorbs this interference:
     T = Az₁⊙Bz₂ + Az₂⊙Bz₁ - u₁Cz₂ - u₂Cz₁
     Think of it as the correction factor that keeps
     the combined system valid."

    DURATION: ~130 seconds
    """

    def construct(self):
        box1 = InstanceBox("Instance\u2081", color=INSTANCE_1_COLOR, u_val="u_1")
        box2 = InstanceBox("Instance\u2082", color=INSTANCE_2_COLOR, u_val="u_2")
        box1.move_to(LEFT * 3 + UP * 1.5)
        box2.move_to(RIGHT * 3 + UP * 1.5)

        self.play(FadeIn(box1), FadeIn(box2), run_time=NORMAL)
        self.wait(0.5)

        question = Text("Can we combine these into one?", font_size=BODY_SIZE, color=WHITE)
        question.to_edge(UP, buff=0.5)
        self.play(Write(question), run_time=NORMAL)
        self.wait(1)

        self.play(FadeOut(question))
        t_label = MathTex("T", font_size=TITLE_SIZE, color=CROSS_TERM_COLOR)
        t_label.move_to(ORIGIN + UP * 1.5)

        arrow1 = Arrow(box1.get_right(), t_label.get_left(), color=INSTANCE_1_COLOR, buff=0.2)
        arrow2 = Arrow(box2.get_left(), t_label.get_right(), color=INSTANCE_2_COLOR, buff=0.2)

        self.play(Create(arrow1), Create(arrow2), FadeIn(t_label), run_time=SLOW)
        self.wait(0.5)

        t_formula = MathTex(
            r"T = Az_1 \circ Bz_2 + Az_2 \circ Bz_1 - u_1 Cz_2 - u_2 Cz_1",
            font_size=LABEL_SIZE,
            color=CROSS_TERM_COLOR,
        )
        t_formula.move_to(DOWN * 2.0)
        self.play(Write(t_formula), run_time=SLOW)
        self.wait(1)

        caption = Text(
            "The correction factor for quadratic interference",
            font_size=SMALL_SIZE,
            color=GREY_B,
        )
        caption.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(caption), run_time=FAST)
        self.wait(2)

        self.play(
            FadeOut(box1),
            FadeOut(box2),
            FadeOut(arrow1),
            FadeOut(arrow2),
            FadeOut(t_label),
            FadeOut(t_formula),
            FadeOut(caption),
        )


class TheFold(Scene):
    """Scene 2.5: Two instances merge into one.

    NARRATION:
    "Now we fold. A random challenge r comes from hashing the transcript.
     Everything combines via random linear combination:
     E prime equals E₁ plus r times T plus r squared times E₂.
     u prime equals u₁ plus r times u₂.
     x prime equals x₁ plus r times x₂.
     W prime equals W₁ plus r times W₂.
     Two instances become one. Same size. Still valid."

    DURATION: ~90 seconds
    CLIP: ZKProof talk — the fold visual
    """

    def construct(self):
        box1 = InstanceBox("Instance\u2081", color=INSTANCE_1_COLOR, u_val="u_1")
        box2 = InstanceBox("Instance\u2082", color=INSTANCE_2_COLOR, u_val="u_2")
        box1.move_to(LEFT * 3)
        box2.move_to(RIGHT * 3)
        self.play(FadeIn(box1), FadeIn(box2), run_time=NORMAL)
        self.wait(0.5)

        r_tex = MathTex(
            r"r \leftarrow H(\pi)",
            font_size=LABEL_SIZE,
            color=WITNESS_COLOR,
        )
        r_tex.to_edge(UP, buff=0.5)
        self.play(Write(r_tex), run_time=NORMAL)
        self.wait(0.5)

        fold_eqs = (
            VGroup(
                MathTex(
                    r"E' = E_1 + r \cdot T + r^2 \cdot E_2",
                    font_size=LABEL_SIZE,
                    color=CROSS_TERM_COLOR,
                ),
                MathTex(r"u' = u_1 + r \cdot u_2", font_size=LABEL_SIZE, color=FOLDED_COLOR),
                MathTex(r"x' = x_1 + r \cdot x_2", font_size=LABEL_SIZE, color=WHITE),
                MathTex(r"W' = W_1 + r \cdot W_2", font_size=LABEL_SIZE, color=WITNESS_COLOR),
            )
            .arrange(DOWN, buff=0.15)
            .to_edge(DOWN, buff=0.5)
        )

        for eq in fold_eqs:
            self.play(Write(eq), run_time=FAST)
        self.wait(1)

        folded_box = InstanceBox("Folded", color=FOLDED_COLOR, u_val="u'")
        folded_box.move_to(ORIGIN)

        self.play(
            box1.animate.move_to(ORIGIN),
            box2.animate.move_to(ORIGIN),
            run_time=SLOW,
        )
        self.play(
            FadeOut(box1),
            FadeOut(box2),
            FadeIn(folded_box),
            Flash(folded_box, color=FOLDED_COLOR, flash_radius=1.5),
            run_time=NORMAL,
        )
        self.wait(0.5)

        result = Text(
            "Same size. Encodes both. Still valid.",
            font_size=BODY_SIZE,
            color=WHITE,
        )
        result.next_to(folded_box, UP, buff=0.5)
        self.play(Write(result), run_time=NORMAL)
        self.wait(2)

        self.play(FadeOut(folded_box), FadeOut(result), FadeOut(fold_eqs), FadeOut(r_tex))
