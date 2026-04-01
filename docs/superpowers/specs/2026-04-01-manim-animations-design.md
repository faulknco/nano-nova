# Nova Educational Animation Series — Design Spec

## Goal

Three Manim Community Edition animations building from R1CS fundamentals to IVC, using hybrid 3B1B + diagram overlay visual style. Designed for YouTube (5-8 min each) with extractable 30-60s clips for ZKProof 8 talk. Narration scripts in code comments, silent renders, ElevenLabs VO added in post-production.

## Visual Style

Hybrid: 3Blue1Brown dark background aesthetic (colored geometric shapes, smooth transforms) with labeled diagram overlays (boxes, arrows, protocol annotations) for technical flow. Uses ManimCE default color palette (BLUE_C, GREEN_C, YELLOW_C, RED_C) plus purple (#bb86fc) for folded/combined results.

## Animation 1: "What is R1CS?" (~5 min)

### Scenes

**Scene 1.1 — Intro (30s):** "A computation is a set of constraints." Show a simple equation a + b = c with numbers, then reveal it's secretly a matrix equation. Text fades: "But how do we prove we know the answer... without revealing it?"

**Scene 1.2 — R1CS Revealed (90s):** Az . Bz = Cz animated step by step:
- Matrices A, B, C appear as colored grids (A=blue, B=green, C=red)
- Vector z appears as a yellow vertical stack of numbers
- Az computed: matrix rows dot with z, results appear as a blue vector
- Bz computed: same animation in green
- Hadamard product Az⊙Bz: element-wise multiplication with "spark" effect
- Cz computed in red
- Final check: equality verified element by element with checkmarks

**Scene 1.3 — Fibonacci Example (90s):** Use the actual nanoNova Fibonacci circuit:
- Show the computation: (1,1) → (1,2) meaning b becomes first, a+b becomes second
- Reveal the 3×6 matrices A, B, C with their actual values
- z = (1, 1, 1, 1, 2, 2) — walk through each constraint being satisfied
- Highlight: "3 constraints, 6 variables, the witness w=[2] is the secret"

**Scene 1.4 — The Relaxation (60s):**
- Start with Az⊙Bz = Cz
- "What if we could combine two of these?"
- Introduce scalar u: Az⊙Bz = u·Cz
- Introduce error E: Az⊙Bz = u·Cz + E
- Show that u=1, E=0 recovers standard R1CS
- Tease: "When u≠1 and E≠0... something powerful happens"
- Fade to: "Next: Nova Folding"

### Key Visuals
- Matrix grids with colored cells (3×6 for Fibonacci)
- Vectors as vertical number stacks
- Hadamard product as element-wise spark/flash
- Equation building up piece by piece

## Animation 2: "Nova Folding — Two Become One" (~6 min)

### Scenes

**Scene 2.1 — Recap (20s):** Quick flash of Relaxed R1CS equation from Animation 1. "We have Az⊙Bz = u·Cz + E. Now the fun begins."

**Scene 2.2 — The Problem (40s):** Two valid Relaxed R1CS instance boxes side by side, each with their own (com_E, u, x, com_W). "We have two valid instances. Can we combine them into one... without losing validity?"

**Scene 2.3 — Cross-Term T (90s):**
- "When we combine quadratic constraints, interference appears"
- Show the expansion: (inst₁ + r·inst₂)² has cross-terms
- Animate T = Az₁⊙Bz₂ + Az₂⊙Bz₁ - u₁·Cz₂ - u₂·Cz₁
- T is the "correction factor" — a bridge vector between the two instances
- Commit to T: show hash arrow from T to com_T

**Scene 2.4 — Fiat-Shamir Challenge (45s):**
- "The verifier needs to send a random challenge. But there's no verifier!"
- Show transcript: com_T, x₁, x₂, u₁, u₂, com_W₁, com_W₂ flowing into a hash function
- Out pops r — a random field element
- "Deterministic randomness from a hash. The verifier's coin flip, without the verifier."

**Scene 2.5 — The Fold (90s):**
- The core animation — two instance boxes sliding toward each other
- Show each fold equation appearing:
  - E' = E₁ + r·T + r²·E₂ (error vectors combining)
  - u' = u₁ + r·u₂ (scalars combining)
  - x' = x₁ + r·x₂ (public inputs combining)
  - W' = W₁ + r·W₂ (witnesses combining)
- Flash: the two boxes merge into one purple box
- "Same size as either input. But encodes BOTH."

**Scene 2.6 — Verification (30s):**
- Show the folded instance going through the Relaxed R1CS check
- Checkmark: "Valid. We started with two. Now we have one."

### Key Visuals
- Instance boxes: rounded rectangles with labeled fields (com_E, u, x, com_W)
- Cross-term T as a glowing bridge between the two boxes
- Hash function as a funnel/grinder visual
- Fold merge: two boxes slide together with a purple flash

## Animation 3: "IVC — A Thousand Steps, One Check" (~7 min)

### Scenes

**Scene 3.1 — The Dream (30s):** "Imagine proving you computed f(x) a thousand times correctly. The verifier checks once." Show a long timeline z₀ → z₁ → ... → z₁₀₀₀ scrolling past.

**Scene 3.2 — The Accumulator (45s):**
- Start with the trivial instance: u=0, E=0, W=0, x=0
- "An empty bucket. It satisfies the relaxed relation trivially — everything is zero."
- Show it as a dim, empty orb/box

**Scene 3.3 — Step by Step (120s):**
- Animate 5-6 fold steps visually:
  - Step 1: Fresh instance appears (bright), gets folded into accumulator (dim→lit)
  - Step 2: Another fresh instance, fold again. Accumulator stays same size but glows brighter.
  - Steps 3-6: Faster, showing the rhythm. Counter increments: 1, 2, 3, 4, 5, 6...
- Key insight: "The accumulator absorbs each step. It never grows."

**Scene 3.4 — Fibonacci Demo (90s):**
- Use actual values from nanoNova: z₀=(1,1)
- Show the sequence: (1,1)→(1,2)→(2,3)→(3,5)→(5,8)→(8,13)→...→(89,144)
- Each step: show z_current, the fresh R1CS instance, and the fold
- After 10 steps: "The accumulator has absorbed 10 Fibonacci steps"
- Verification check: one Relaxed R1CS evaluation. Checkmark.

**Scene 3.5 — The Punchline (60s):**
- Split screen: prover work vs verifier work
- Prover: bar chart growing linearly with step count (10, 100, 1000 steps)
- Verifier: flat line — always one check, regardless of steps
- "1000 matrix multiplications for the prover. One check for the verifier."
- "This is Incrementally Verifiable Computation."

### Key Visuals
- Accumulator as a glowing orb/circle that pulses brighter with each fold
- Timeline scrolling left as steps accumulate
- Fresh instances appearing as bright boxes that get absorbed
- Prover/verifier cost comparison as animated bar chart

## Project Structure

```
animations/
├── common/
│   ├── theme.py       # Colors, fonts, shared visual config
│   └── components.py  # Reusable Manim objects
├── scene_01_r1cs.py
├── scene_02_folding.py
├── scene_03_ivc.py
└── media/             # Rendered output (gitignored)
```

## Shared Components (`common/`)

### `theme.py`
- Color constants: MATRIX_A (blue), MATRIX_B (green), MATRIX_C (red), VECTOR_Z (yellow), FOLDED (purple), INSTANCE_1 (blue), INSTANCE_2 (green)
- Font sizes for labels, equations, annotations
- Standard animation durations (fast=0.3s, normal=0.6s, slow=1.0s)
- Background color (3B1B default dark)

### `components.py`
Reusable Manim VGroups/Animations:

- `MatrixGrid(values, color)` — Animated matrix display with colored cells, supports highlighting individual cells/rows/columns, labels
- `VectorStack(values, color)` — Vertical vector with number labels, supports element highlighting
- `InstanceBox(label, fields)` — Rounded rectangle representing a Relaxed R1CS instance with labeled fields (com_E, u, x, com_W)
- `HadamardSpark(vec1, vec2)` — Element-wise "spark" animation for Hadamard product
- `FoldMerge(box1, box2, result)` — Two boxes sliding together and merging into one with a flash
- `AccumulatorOrb(brightness)` — Glowing circle that can pulse brighter on fold steps

## Dependencies

```bash
uv add --dev manim
```

ManimCE requires: cairo, pango, ffmpeg (all available via brew on macOS).

## Render Commands

```bash
cd ~/Projects/nano-nova
manim render animations/scene_01_r1cs.py -pqh         # preview, high quality (1080p)
manim render animations/scene_01_r1cs.py -qk           # 4K final render
manim render animations/scene_01_r1cs.py R1CSIntro -pql # preview single scene, low quality (fast)
```

## Narration Script Format

Scripts embedded as docstrings/comments in each Scene class:

```python
class R1CSIntro(Scene):
    """
    NARRATION:
    "A computation is a set of constraints.
     You've probably seen equations like a + b = c.
     But in zero-knowledge proofs, we encode computations differently..."

    DURATION: ~30 seconds
    CLIP: ZKProof talk slide 3
    """
```

## Out of Scope

- Animations 4-5 (norm growth, scheme comparison) — Spec 2 after sweep data
- Voiceover audio rendering (ElevenLabs in post-production)
- Video editing, cuts, transitions between animations
- Background music
- Thumbnail/title card design
- YouTube upload/metadata
