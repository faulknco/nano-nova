# Nova Educational Animation Series Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three Manim animations (R1CS → Folding → IVC) in hybrid 3B1B + diagram overlay style, with narration scripts and reusable components.

**Architecture:** Shared theme/components in `animations/common/`, one Python file per animation scene. Each scene is a Manim `Scene` subclass rendered independently. Components are reusable VGroups (MatrixGrid, VectorStack, InstanceBox, etc.) tested via preview renders.

**Tech Stack:** ManimCE (Manim Community Edition), Python 3.12+

**Spec:** `docs/superpowers/specs/2026-04-01-manim-animations-design.md`

**Verification:** Since these are visual outputs, "testing" means rendering with `manim render <file> <Scene> -pql` (preview, low quality) and visually confirming the output. No pytest for animation code.

---

### Task 1: Setup and Dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `animations/common/__init__.py`
- Create: `animations/common/theme.py`
- Create: `animations/__init__.py`

- [ ] **Step 1: Install ManimCE**

Run: `cd ~/Projects/nano-nova && uv add --dev manim`

If brew dependencies are missing:
```bash
brew install cairo pango ffmpeg
```

- [ ] **Step 2: Verify Manim works**

Run: `cd ~/Projects/nano-nova && uv run manim --version`
Expected: Manim Community v0.x.x

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p ~/Projects/nano-nova/animations/common
touch ~/Projects/nano-nova/animations/__init__.py
touch ~/Projects/nano-nova/animations/common/__init__.py
```

- [ ] **Step 4: Create theme.py**

```python
# animations/common/theme.py
"""Shared visual theme for nanoNova animations.

Hybrid style: 3B1B dark background with diagram overlay labels.
"""

from manim import (
    BLUE_C, GREEN_C, RED_C, YELLOW_C,
    WHITE, GREY_B, GREY_D,
    DEFAULT_FONT_SIZE,
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
```

- [ ] **Step 5: Test theme imports**

Run: `cd ~/Projects/nano-nova && uv run python -c "from animations.common.theme import *; print('Theme OK')"`
Expected: `Theme OK`

- [ ] **Step 6: Add media/ to gitignore**

Append to `.gitignore` (create if needed):
```
animations/media/
```

- [ ] **Step 7: Commit**

```bash
cd ~/Projects/nano-nova && git add animations/ pyproject.toml uv.lock .gitignore && git commit -m "feat(anim): setup ManimCE + theme config for animation series"
```

---

### Task 2: Shared Components — MatrixGrid and VectorStack

**Files:**
- Create: `animations/common/components.py`

These are the foundational visual building blocks used across all 3 animations.

- [ ] **Step 1: Implement MatrixGrid**

```python
# animations/common/components.py
"""Reusable Manim components for nanoNova animations."""

from manim import (
    VGroup, Square, Text, MathTex,
    FadeIn, FadeOut, Indicate,
    RIGHT, DOWN, UP, LEFT, ORIGIN,
    WHITE, GREY_D,
)
from .theme import (
    MATRIX_CELL_SIZE, VECTOR_CELL_SIZE, LABEL_SIZE, SMALL_SIZE,
    FAST, NORMAL,
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

        # Center the grid
        self.move_to(ORIGIN)

        # Optional label
        if label:
            self.label = MathTex(label, font_size=LABEL_SIZE, color=color)
            self.label.next_to(self, UP, buff=0.2)
            self.add(self.label)

    def highlight_row(self, row_idx, color, opacity=0.5):
        """Return animations to highlight a row."""
        return [
            cell.animate.set_fill(color, opacity=opacity)
            for cell in self.cells[row_idx]
        ]

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
        from manim import RoundedRectangle

        self.box = RoundedRectangle(
            corner_radius=0.15, width=width, height=height,
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
```

- [ ] **Step 2: Write a preview scene to verify components**

```python
# animations/test_components.py
"""Quick preview of shared components. Not a real animation — just for visual testing."""

from manim import Scene, FadeIn, RIGHT, DOWN
from common.theme import *
from common.components import MatrixGrid, VectorStack, InstanceBox


class ComponentPreview(Scene):
    def construct(self):
        # Matrix A from Fibonacci circuit
        A = MatrixGrid(
            [[1,0,0,0,0,0], [1,0,0,0,0,0], [1,0,0,0,0,0]],
            color=MATRIX_A_COLOR, label="A"
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
        box1 = InstanceBox("Instance₁", color=INSTANCE_1_COLOR, u_val="1")
        box2 = InstanceBox("Instance₂", color=INSTANCE_2_COLOR, u_val="1")
        box1.shift(DOWN * 2 + LEFT * 2)
        box2.shift(DOWN * 2 + RIGHT * 2)
        self.play(FadeIn(box1), FadeIn(box2))
        self.wait(1)
```

- [ ] **Step 3: Render preview**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render test_components.py ComponentPreview -pql`
Expected: Opens a preview window showing the matrix grid, vector stack, and two instance boxes. Verify:
- Matrix cells are colored blue with numbers visible
- Vector is yellow with stacked numbers
- Instance boxes have labels and u values

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/nano-nova && git add animations/ && git commit -m "feat(anim): shared components — MatrixGrid, VectorStack, InstanceBox"
```

---

### Task 3: Animation 1 — "What is R1CS?"

**Files:**
- Create: `animations/scene_01_r1cs.py`

- [ ] **Step 1: Implement Scene 1.1 — Intro**

```python
# animations/scene_01_r1cs.py
"""Animation 1: What is R1CS?

NARRATION OVERVIEW:
A computation is a set of constraints. We encode them as matrices.
R1CS lets us prove we know a solution without revealing it.
Then we "relax" the system to enable something powerful: folding.

DURATION: ~5 minutes total
CLIPS FOR ZKPROOF 8: Scenes 1.2 (R1CS equation) and 1.4 (relaxation)
"""

from manim import (
    Scene, Text, MathTex, VGroup,
    FadeIn, FadeOut, Write, Transform, TransformMatchingTex,
    ReplacementTransform, Indicate, Create, Uncreate,
    LEFT, RIGHT, UP, DOWN, ORIGIN,
    WHITE, GREY_B,
)
from common.theme import *
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
        # Title
        title = Text("What is R1CS?", font_size=TITLE_SIZE, color=WHITE)
        subtitle = Text(
            "Rank-1 Constraint System",
            font_size=HEADING_SIZE, color=GREY_B
        )
        subtitle.next_to(title, DOWN, buff=0.3)
        self.play(Write(title), run_time=SLOW)
        self.play(FadeIn(subtitle), run_time=NORMAL)
        self.wait(1)

        # Simple equation
        self.play(FadeOut(title), FadeOut(subtitle))
        eq = MathTex("a + b = c", font_size=TITLE_SIZE, color=WITNESS_COLOR)
        self.play(Write(eq), run_time=SLOW)
        self.wait(1)

        # "But what if there are thousands?"
        question = Text(
            "What if there are thousands of these?",
            font_size=BODY_SIZE, color=GREY_B,
        )
        question.next_to(eq, DOWN, buff=0.5)
        self.play(FadeIn(question), run_time=NORMAL)
        self.wait(1)

        # Transition
        self.play(FadeOut(eq), FadeOut(question))
        answer = Text(
            "We encode them as matrix equations.",
            font_size=BODY_SIZE, color=WHITE,
        )
        self.play(Write(answer), run_time=NORMAL)
        self.wait(1)
        self.play(FadeOut(answer))
```

- [ ] **Step 2: Render and verify Scene 1.1**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_01_r1cs.py R1CSIntro -pql`
Expected: Title appears, equation fades in, question appears, transitions cleanly.

- [ ] **Step 3: Implement Scene 1.2 — R1CS Equation**

```python
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
        # Show the equation building up
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

        # Move equation to top
        full_eq = VGroup(eq1, dot, eq2, equals, eq3)
        self.play(full_eq.animate.to_edge(UP, buff=0.5).scale(0.7), run_time=NORMAL)

        # Show Fibonacci matrices
        A_vals = [[1,0,0,0,0,0], [1,0,0,0,0,0], [1,0,0,0,0,0]]
        B_vals = [[0,1,1,0,0,0], [0,0,1,0,0,0], [0,0,0,0,0,1]]
        C_vals = [[0,0,0,0,0,1], [0,0,0,1,0,0], [0,0,0,0,1,0]]

        A_grid = MatrixGrid(A_vals, color=MATRIX_A_COLOR, label="A")
        B_grid = MatrixGrid(B_vals, color=MATRIX_B_COLOR, label="B")
        C_grid = MatrixGrid(C_vals, color=MATRIX_C_COLOR, label="C")

        A_grid.scale(0.6).move_to(LEFT * 4 + DOWN * 0.5)
        B_grid.scale(0.6).move_to(DOWN * 0.5)
        C_grid.scale(0.6).move_to(RIGHT * 4 + DOWN * 0.5)

        self.play(FadeIn(A_grid), FadeIn(B_grid), FadeIn(C_grid), run_time=SLOW)
        self.wait(1)

        # Show vector z
        z = VectorStack([1, 1, 1, 1, 2, 2], color=VECTOR_Z_COLOR, label="z")
        z.scale(0.5).move_to(DOWN * 3)
        z_label = Text(
            "z = (1, a, b, b, a+b, w)",
            font_size=SMALL_SIZE, color=VECTOR_Z_COLOR,
        )
        z_label.next_to(z, DOWN, buff=0.2)
        self.play(FadeIn(z), FadeIn(z_label), run_time=NORMAL)
        self.wait(2)

        self.play(
            FadeOut(A_grid), FadeOut(B_grid), FadeOut(C_grid),
            FadeOut(z), FadeOut(z_label), FadeOut(full_eq),
        )
```

- [ ] **Step 4: Render and verify Scene 1.2**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_01_r1cs.py R1CSEquation -pql`
Expected: Equation builds up, matrices appear with colored grids, z vector appears below.

- [ ] **Step 5: Implement Scene 1.4 — The Relaxation**

```python
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
        # Standard R1CS
        standard = MathTex(
            r"A\vec{z}", r"\circ", r"B\vec{z}", "=", r"C\vec{z}",
            font_size=HEADING_SIZE,
        )
        standard[0].set_color(MATRIX_A_COLOR)
        standard[2].set_color(MATRIX_B_COLOR)
        standard[4].set_color(MATRIX_C_COLOR)
        self.play(Write(standard), run_time=SLOW)
        self.wait(1)

        # Question
        q = Text("Can we combine two of these?", font_size=BODY_SIZE, color=GREY_B)
        q.next_to(standard, DOWN, buff=0.5)
        self.play(FadeIn(q), run_time=NORMAL)
        self.wait(1)
        self.play(FadeOut(q))

        # Transform to relaxed
        relaxed = MathTex(
            r"A\vec{z}", r"\circ", r"B\vec{z}", "=",
            "u", r"\cdot", r"C\vec{z}", "+", r"\vec{E}",
            font_size=HEADING_SIZE,
        )
        relaxed[0].set_color(MATRIX_A_COLOR)
        relaxed[2].set_color(MATRIX_B_COLOR)
        relaxed[4].set_color(FOLDED_COLOR)  # u
        relaxed[6].set_color(MATRIX_C_COLOR)
        relaxed[8].set_color(CROSS_TERM_COLOR)  # E
        self.play(TransformMatchingTex(standard, relaxed), run_time=VERY_SLOW)
        self.wait(1)

        # Annotations
        u_note = Text("u = 1 for real instances", font_size=SMALL_SIZE, color=FOLDED_COLOR)
        e_note = Text("E = 0 for real instances", font_size=SMALL_SIZE, color=CROSS_TERM_COLOR)
        u_note.next_to(relaxed, DOWN, buff=0.5)
        e_note.next_to(u_note, DOWN, buff=0.2)
        self.play(FadeIn(u_note), FadeIn(e_note), run_time=NORMAL)
        self.wait(1)

        # Tease
        tease = Text(
            "When u ≠ 1 and E ≠ 0... folding happens.",
            font_size=BODY_SIZE, color=WHITE,
        )
        self.play(FadeOut(u_note), FadeOut(e_note))
        tease.next_to(relaxed, DOWN, buff=0.5)
        self.play(Write(tease), run_time=SLOW)
        self.wait(2)

        self.play(FadeOut(relaxed), FadeOut(tease))
```

- [ ] **Step 6: Render and verify Scene 1.4**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_01_r1cs.py R1CSRelaxation -pql`
Expected: Standard equation transforms into relaxed form with u (purple) and E (red) appearing. Annotations fade in below.

- [ ] **Step 7: Commit**

```bash
cd ~/Projects/nano-nova && git add animations/scene_01_r1cs.py && git commit -m "feat(anim): Animation 1 — What is R1CS? (3 scenes)"
```

---

### Task 4: Animation 2 — "Nova Folding — Two Become One"

**Files:**
- Create: `animations/scene_02_folding.py`

- [ ] **Step 1: Implement Scene 2.2+2.3 — The Problem + Cross-Term**

```python
# animations/scene_02_folding.py
"""Animation 2: Nova Folding — Two Become One.

NARRATION OVERVIEW:
Two valid constraint instances. Can we combine them into one?
The cross-term T absorbs the interference from quadratic constraints.
A Fiat-Shamir challenge provides verifier randomness without a verifier.
The fold merges everything: E, u, x, W — same size output as input.

DURATION: ~6 minutes total
CLIPS FOR ZKPROOF 8: Scene 2.5 (the fold animation)
"""

from manim import (
    Scene, Text, MathTex, VGroup, Arrow,
    FadeIn, FadeOut, Write, Create,
    ReplacementTransform, Indicate, Flash,
    LEFT, RIGHT, UP, DOWN, ORIGIN,
    WHITE, GREY_B,
)
from common.theme import *
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
        # Two instance boxes
        box1 = InstanceBox("Instance₁", color=INSTANCE_1_COLOR, u_val="u_1")
        box2 = InstanceBox("Instance₂", color=INSTANCE_2_COLOR, u_val="u_2")
        box1.move_to(LEFT * 3)
        box2.move_to(RIGHT * 3)

        self.play(FadeIn(box1), FadeIn(box2), run_time=NORMAL)
        self.wait(0.5)

        question = Text("Can we combine these into one?", font_size=BODY_SIZE, color=WHITE)
        question.to_edge(UP, buff=0.5)
        self.play(Write(question), run_time=NORMAL)
        self.wait(1)

        # Cross-term T appears between them
        self.play(FadeOut(question))
        t_label = MathTex("T", font_size=TITLE_SIZE, color=CROSS_TERM_COLOR)
        t_label.move_to(ORIGIN + UP * 0.5)

        # Bridge arrows
        arrow1 = Arrow(box1.get_right(), t_label.get_left(), color=INSTANCE_1_COLOR, buff=0.2)
        arrow2 = Arrow(box2.get_left(), t_label.get_right(), color=INSTANCE_2_COLOR, buff=0.2)

        self.play(Create(arrow1), Create(arrow2), FadeIn(t_label), run_time=SLOW)
        self.wait(0.5)

        # Cross-term formula
        t_formula = MathTex(
            r"T = Az_1 \circ Bz_2 + Az_2 \circ Bz_1 - u_1 Cz_2 - u_2 Cz_1",
            font_size=LABEL_SIZE, color=CROSS_TERM_COLOR,
        )
        t_formula.next_to(t_label, DOWN, buff=0.3)
        self.play(Write(t_formula), run_time=SLOW)
        self.wait(1)

        caption = Text(
            "The correction factor for quadratic interference",
            font_size=SMALL_SIZE, color=GREY_B,
        )
        caption.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(caption), run_time=FAST)
        self.wait(2)

        self.play(
            FadeOut(box1), FadeOut(box2),
            FadeOut(arrow1), FadeOut(arrow2),
            FadeOut(t_label), FadeOut(t_formula), FadeOut(caption),
        )
```

- [ ] **Step 2: Render and verify**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_02_folding.py FoldingSetup -pql`
Expected: Two instance boxes with arrows pointing to T in the middle. Formula appears below T.

- [ ] **Step 3: Implement Scene 2.5 — The Fold**

```python
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
        # Two boxes, positioned for merging
        box1 = InstanceBox("Instance₁", color=INSTANCE_1_COLOR, u_val="u_1")
        box2 = InstanceBox("Instance₂", color=INSTANCE_2_COLOR, u_val="u_2")
        box1.move_to(LEFT * 3)
        box2.move_to(RIGHT * 3)
        self.play(FadeIn(box1), FadeIn(box2), run_time=NORMAL)
        self.wait(0.5)

        # Challenge r
        r_tex = MathTex(r"r \leftarrow H(\text{transcript})", font_size=LABEL_SIZE, color=WITNESS_COLOR)
        r_tex.to_edge(UP, buff=0.5)
        self.play(Write(r_tex), run_time=NORMAL)
        self.wait(0.5)

        # Fold equations appearing one by one
        fold_eqs = VGroup(
            MathTex(r"E' = E_1 + r \cdot T + r^2 \cdot E_2", font_size=LABEL_SIZE, color=CROSS_TERM_COLOR),
            MathTex(r"u' = u_1 + r \cdot u_2", font_size=LABEL_SIZE, color=FOLDED_COLOR),
            MathTex(r"x' = x_1 + r \cdot x_2", font_size=LABEL_SIZE, color=WHITE),
            MathTex(r"W' = W_1 + r \cdot W_2", font_size=LABEL_SIZE, color=WITNESS_COLOR),
        ).arrange(DOWN, buff=0.15).to_edge(DOWN, buff=0.5)

        for eq in fold_eqs:
            self.play(Write(eq), run_time=FAST)
        self.wait(1)

        # THE MERGE — boxes slide together
        folded_box = InstanceBox("Folded", color=FOLDED_COLOR, u_val="u'")
        folded_box.move_to(ORIGIN)

        self.play(
            box1.animate.move_to(ORIGIN),
            box2.animate.move_to(ORIGIN),
            run_time=SLOW,
        )
        self.play(
            FadeOut(box1), FadeOut(box2),
            FadeIn(folded_box),
            Flash(folded_box, color=FOLDED_COLOR, flash_radius=1.5),
            run_time=NORMAL,
        )
        self.wait(0.5)

        # Result text
        result = Text(
            "Same size. Encodes both. Still valid.",
            font_size=BODY_SIZE, color=WHITE,
        )
        result.next_to(folded_box, UP, buff=0.5)
        self.play(Write(result), run_time=NORMAL)
        self.wait(2)

        self.play(FadeOut(folded_box), FadeOut(result), FadeOut(fold_eqs), FadeOut(r_tex))
```

- [ ] **Step 4: Render and verify**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_02_folding.py TheFold -pql`
Expected: Two boxes slide together, flash purple, fold equations appear below. "Same size. Encodes both. Still valid."

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add animations/scene_02_folding.py && git commit -m "feat(anim): Animation 2 — Nova Folding (setup + fold scenes)"
```

---

### Task 5: Animation 3 — "IVC — A Thousand Steps, One Check"

**Files:**
- Create: `animations/scene_03_ivc.py`

- [ ] **Step 1: Implement Scene 3.3 — Step by Step Accumulation**

```python
# animations/scene_03_ivc.py
"""Animation 3: IVC — A Thousand Steps, One Check.

NARRATION OVERVIEW:
The dream: prove f(x) applied 1000 times with one verifier check.
An accumulator starts empty, absorbs each step via folding.
The Fibonacci sequence demonstrates it with real numbers.
Prover work grows linearly. Verifier work is constant.

DURATION: ~7 minutes total
CLIPS FOR ZKPROOF 8: Scene 3.5 (prover vs verifier cost)
"""

from manim import (
    Scene, Text, MathTex, VGroup, Circle,
    FadeIn, FadeOut, Write, Create, Flash,
    LEFT, RIGHT, UP, DOWN, ORIGIN,
    WHITE, GREY_B, GREY_D,
    BarChart,
)
from common.theme import *
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
        # Title
        title = Text("IVC: Incrementally Verifiable Computation", font_size=HEADING_SIZE, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=NORMAL)

        # Accumulator orb
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

        # Fold loop — 6 steps, speeding up
        step_times = [SLOW, SLOW, NORMAL, NORMAL, FAST, FAST]
        opacity_steps = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65]

        for i, (time, opacity) in enumerate(zip(step_times, opacity_steps)):
            step_num = i + 1

            # Fresh instance appears on the right
            fresh = InstanceBox(f"Step {step_num}", color=FRESH_INSTANCE_COLOR, width=1.8, height=1.0)
            fresh.move_to(RIGHT * 3)
            self.play(FadeIn(fresh), run_time=time)

            # Slides into accumulator
            self.play(
                fresh.animate.move_to(acc.get_center()),
                run_time=time,
            )
            self.play(
                FadeOut(fresh),
                acc.animate.set_fill(ACCUMULATOR_COLOR, opacity=opacity),
                Flash(acc, color=ACCUMULATOR_COLOR, flash_radius=0.8),
                run_time=time * 0.5,
            )

            # Update counter
            new_counter = Text(f"Steps: {step_num}", font_size=BODY_SIZE, color=WHITE)
            new_counter.to_edge(DOWN, buff=0.5)
            self.play(FadeOut(counter), FadeIn(new_counter), run_time=FAST * 0.5)
            counter = new_counter

        self.wait(1)

        # "Still one instance"
        note = Text(
            "6 steps absorbed. Still one instance.",
            font_size=BODY_SIZE, color=WHITE,
        )
        note.next_to(acc_group, DOWN, buff=0.8)
        self.play(Write(note), run_time=NORMAL)
        self.wait(2)

        self.play(FadeOut(acc_group), FadeOut(counter), FadeOut(note), FadeOut(title))
```

- [ ] **Step 2: Render and verify**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_03_ivc.py IVCAccumulation -pql`
Expected: Accumulator circle absorbs 6 fresh instances. Grows brighter with each fold. Counter increments. Animation speeds up.

- [ ] **Step 3: Implement Scene 3.5 — The Punchline (Prover vs Verifier)**

```python
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

        # Bar chart — prover cost
        steps = [10, 100, 1000]
        prover_label = Text("Prover (folds)", font_size=LABEL_SIZE, color=INSTANCE_1_COLOR)
        verifier_label = Text("Verifier (checks)", font_size=LABEL_SIZE, color=CHECKMARK_COLOR)

        # Manual bar chart with rectangles
        from manim import Rectangle

        bar_group = VGroup()
        x_positions = [-3, 0, 3]

        for x_pos, step_count in zip(x_positions, steps):
            # Prover bar (height proportional to steps)
            p_height = step_count / 300  # normalize to max ~3.3
            p_bar = Rectangle(width=0.8, height=p_height, color=INSTANCE_1_COLOR)
            p_bar.set_fill(INSTANCE_1_COLOR, opacity=0.6)
            p_bar.move_to([x_pos - 0.5, p_height / 2 - 1.5, 0])

            # Verifier bar (always 1 check)
            v_height = 0.1
            v_bar = Rectangle(width=0.8, height=v_height, color=CHECKMARK_COLOR)
            v_bar.set_fill(CHECKMARK_COLOR, opacity=0.6)
            v_bar.move_to([x_pos + 0.5, v_height / 2 - 1.5, 0])

            # Label
            label = Text(f"{step_count}", font_size=SMALL_SIZE, color=WHITE)
            label.move_to([x_pos, -2.0, 0])

            bar_group.add(p_bar, v_bar, label)

        x_axis_label = Text("Number of computation steps", font_size=SMALL_SIZE, color=GREY_B)
        x_axis_label.move_to(DOWN * 2.5)
        bar_group.add(x_axis_label)

        self.play(FadeIn(bar_group), run_time=SLOW)
        self.wait(1)

        # Legend
        legend = VGroup(prover_label, verifier_label).arrange(RIGHT, buff=1)
        legend.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(legend), run_time=FAST)
        self.wait(1)

        # Punchline text
        punchline = Text(
            "1000 folds for the prover. 1 check for the verifier.",
            font_size=BODY_SIZE, color=WHITE,
        )
        punchline.to_edge(DOWN, buff=0.3)
        self.play(Write(punchline), run_time=SLOW)
        self.wait(2)

        self.play(FadeOut(bar_group), FadeOut(legend), FadeOut(punchline), FadeOut(title))

        # Final card
        final = Text(
            "This is Incrementally Verifiable Computation.",
            font_size=HEADING_SIZE, color=FOLDED_COLOR,
        )
        self.play(Write(final), run_time=VERY_SLOW)
        self.wait(2)
        self.play(FadeOut(final))
```

- [ ] **Step 4: Render and verify**

Run: `cd ~/Projects/nano-nova/animations && uv run manim render scene_03_ivc.py IVCPunchline -pql`
Expected: Bar chart with prover bars growing (10→100→1000) but verifier bars staying tiny. Punchline text.

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add animations/scene_03_ivc.py && git commit -m "feat(anim): Animation 3 — IVC accumulation + prover vs verifier cost"
```

---

### Task 6: Full Render and Polish

**Files:**
- All animation files

- [ ] **Step 1: Render all scenes in high quality (1080p)**

```bash
cd ~/Projects/nano-nova/animations
uv run manim render scene_01_r1cs.py -qh
uv run manim render scene_02_folding.py -qh
uv run manim render scene_03_ivc.py -qh
```

Expected: MP4 files in `animations/media/videos/*/1080p60/`

- [ ] **Step 2: Watch each render, note timing/pacing issues**

Review each video. Check:
- Text readable at 1080p
- Animations not too fast or too slow
- Color contrast sufficient
- Transitions smooth between scenes

- [ ] **Step 3: Fix any visual issues found**

Adjust timing constants, positions, font sizes as needed. Re-render affected scenes.

- [ ] **Step 4: Render 4K final versions**

```bash
cd ~/Projects/nano-nova/animations
uv run manim render scene_01_r1cs.py -qk
uv run manim render scene_02_folding.py -qk
uv run manim render scene_03_ivc.py -qk
```

- [ ] **Step 5: Final commit**

```bash
cd ~/Projects/nano-nova && git add animations/ && git commit -m "feat(anim): complete Nova educational animation series (3 animations, 6 scenes)"
```

---

### Task Summary

| Task | Files | Scenes | Description |
|------|-------|--------|-------------|
| 1 | theme.py, setup | — | ManimCE install, theme, gitignore |
| 2 | components.py | preview | MatrixGrid, VectorStack, InstanceBox |
| 3 | scene_01_r1cs.py | 3 scenes | R1CS intro, equation, relaxation |
| 4 | scene_02_folding.py | 2 scenes | Cross-term + the fold merge |
| 5 | scene_03_ivc.py | 2 scenes | Accumulation + prover vs verifier |
| 6 | all | — | Full render, polish, 4K output |
