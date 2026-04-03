"""Animation 3: IVC — A Thousand Steps, One Check.

NARRATION OVERVIEW:
The dream: prove f(x) applied 1000 times with one verifier check.
An accumulator starts empty, absorbs each step via folding.
The Fibonacci sequence demonstrates it with real numbers.
Prover work grows linearly. Verifier work is constant.

DURATION: ~7 minutes total
CLIPS FOR ZKPROOF 8: Scene 3.5 (prover vs verifier cost)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from manim import (
    Scene,
    Text,
    VGroup,
    Circle,
    Rectangle,
    FadeIn,
    FadeOut,
    Write,
    Flash,
    LEFT,
    RIGHT,
    UP,
    DOWN,
    WHITE,
    GREY_B,
)
from common.theme import (
    HEADING_SIZE,
    BODY_SIZE,
    LABEL_SIZE,
    SMALL_SIZE,
    SLOW,
    NORMAL,
    FAST,
    VERY_SLOW,
    ACCUMULATOR_COLOR,
    FRESH_INSTANCE_COLOR,
    FOLDED_COLOR,
    INSTANCE_1_COLOR,
    CHECKMARK_COLOR,
)
from common.components import InstanceBox


class IVCAccumulation(Scene):
    """Scene 3.2-3.3: The accumulator absorbs each step.

    NARRATION:
    "We start with an empty accumulator — u is zero, E is zero,
     everything is zero. It satisfies the relaxed relation trivially.
     Now watch: a fresh computation step arrives.
     We fold it into the accumulator.
     Another step. Fold again.
     The accumulator stays the same size,
     but it now encodes ALL previous steps.
     After 10 steps, after 100, after 1000 —
     the accumulator is still one instance."

    DURATION: ~120 seconds
    """

    def construct(self):
        title = Text(
            "IVC: Incrementally Verifiable Computation", font_size=HEADING_SIZE, color=WHITE
        )
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=NORMAL)

        acc = Circle(radius=0.6, color=ACCUMULATOR_COLOR)
        acc.set_fill(ACCUMULATOR_COLOR, opacity=0.1)
        acc.set_stroke(ACCUMULATOR_COLOR, width=2)
        acc_label = Text("acc", font_size=SMALL_SIZE, color=ACCUMULATOR_COLOR)
        acc_label.move_to(acc.get_center())
        acc_group = VGroup(acc, acc_label)
        acc_group.move_to(LEFT * 2)
        self.play(FadeIn(acc_group), run_time=NORMAL)

        counter = Text("Steps: 0", font_size=BODY_SIZE, color=WHITE)
        counter.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(counter), run_time=FAST)

        step_times = [SLOW, SLOW, NORMAL, NORMAL, FAST, FAST]
        opacity_steps = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65]

        for i, (speed, opacity) in enumerate(zip(step_times, opacity_steps)):
            step_num = i + 1

            fresh = InstanceBox(
                f"Step {step_num}", color=FRESH_INSTANCE_COLOR, width=1.8, height=1.0
            )
            fresh.move_to(RIGHT * 3)
            self.play(FadeIn(fresh), run_time=speed)

            self.play(fresh.animate.move_to(acc.get_center()), run_time=speed)
            self.play(
                FadeOut(fresh),
                acc.animate.set_fill(ACCUMULATOR_COLOR, opacity=opacity),
                Flash(acc, color=ACCUMULATOR_COLOR, flash_radius=0.8),
                run_time=speed * 0.5,
            )

            new_counter = Text(f"Steps: {step_num}", font_size=BODY_SIZE, color=WHITE)
            new_counter.to_edge(DOWN, buff=0.5)
            self.play(FadeOut(counter), FadeIn(new_counter), run_time=FAST * 0.5)
            counter = new_counter

        self.wait(1)

        note = Text("6 steps absorbed. Still one instance.", font_size=BODY_SIZE, color=WHITE)
        note.next_to(acc_group, DOWN, buff=0.8)
        self.play(Write(note), run_time=NORMAL)
        self.wait(2)

        self.play(FadeOut(acc_group), FadeOut(counter), FadeOut(note), FadeOut(title))


class IVCPunchline(Scene):
    """Scene 3.5: Prover work linear, verifier work constant.

    NARRATION:
    "Here's the punchline.
     The prover does one fold per step.
     10 steps? 10 folds. 1000 steps? 1000 folds.
     The work grows linearly.
     But the verifier? The verifier always does ONE check.
     One relaxed R1CS evaluation. That's it.
     10 steps or 10 million — same cost.
     This is the power of IVC through folding."

    DURATION: ~60 seconds
    CLIP: ZKProof talk — cost comparison
    """

    def construct(self):
        title = Text("Prover vs Verifier Cost", font_size=HEADING_SIZE, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=NORMAL)

        prover_label = Text("Prover (folds)", font_size=LABEL_SIZE, color=INSTANCE_1_COLOR)
        verifier_label = Text("Verifier (checks)", font_size=LABEL_SIZE, color=CHECKMARK_COLOR)

        steps = [10, 100, 1000]
        bar_group = VGroup()
        x_positions = [-3, 0, 3]

        for x_pos, step_count in zip(x_positions, steps):
            p_height = step_count / 300
            p_bar = Rectangle(width=0.8, height=p_height, color=INSTANCE_1_COLOR)
            p_bar.set_fill(INSTANCE_1_COLOR, opacity=0.6)
            p_bar.move_to([x_pos - 0.5, p_height / 2 - 1.5, 0])

            v_height = 0.1
            v_bar = Rectangle(width=0.8, height=v_height, color=CHECKMARK_COLOR)
            v_bar.set_fill(CHECKMARK_COLOR, opacity=0.6)
            v_bar.move_to([x_pos + 0.5, v_height / 2 - 1.5, 0])

            label = Text(f"{step_count}", font_size=SMALL_SIZE, color=WHITE)
            label.move_to([x_pos, -2.0, 0])

            bar_group.add(p_bar, v_bar, label)

        x_axis_label = Text("Number of computation steps", font_size=SMALL_SIZE, color=GREY_B)
        x_axis_label.move_to(DOWN * 2.5)
        bar_group.add(x_axis_label)

        self.play(FadeIn(bar_group), run_time=SLOW)
        self.wait(1)

        legend = VGroup(prover_label, verifier_label).arrange(RIGHT, buff=1)
        legend.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(legend), run_time=FAST)
        self.wait(1)

        punchline = Text(
            "1000 folds for the prover. 1 check for the verifier.",
            font_size=BODY_SIZE,
            color=WHITE,
        )
        punchline.to_edge(DOWN, buff=0.3)
        self.play(Write(punchline), run_time=SLOW)
        self.wait(2)

        self.play(FadeOut(bar_group), FadeOut(legend), FadeOut(punchline), FadeOut(title))

        final = Text(
            "This is Incrementally Verifiable Computation.",
            font_size=HEADING_SIZE,
            color=FOLDED_COLOR,
        )
        self.play(Write(final), run_time=VERY_SLOW)
        self.wait(2)
        self.play(FadeOut(final))
