"""
Shared building blocks for the lock visualizations.

Visual vocabulary (the same in every scene):

  * Thread      -- a panel at the bottom showing the thread's code, a program
                   counter (triangle) pointing at the next line to execute,
                   and the thread's private variable ``tmp``.
  * Data        -- a box in shared memory (top) holding a value.
  * Lock        -- a padlock. Grey/open = free; closed and filled with a
                   thread's color = held by that thread.  A solid line in the
                   thread's color connects the lock to its holder; a red
                   dashed line connects it to threads waiting for it.
  * Protection  -- a dashed frame around a lock and the data it protects.
                   It is dashed on purpose: the relation is a programming
                   convention, nothing enforces it.
  * Critical    -- shaded lines of code.  While a thread is inside its
    section        critical section, its panel glows.  If two threads are
                   inside critical sections touching the same data, that
                   data is flagged as a race.
"""
from __future__ import annotations

from manim import *

MONO = "DejaVu Sans Mono"
SANS = "DejaVu Sans"

THREAD_COLORS = [BLUE_C, ORANGE, GREEN_C, PURPLE_B]
FREE_COLOR = GREY_B
BAD = RED_C
SHADE_COLOR = YELLOW_E
CODE_SIZE = 22
LINE_H = 0.39


def mono(s, size=CODE_SIZE, color=WHITE):
    return Text(s, font=MONO, font_size=size, color=color)


def sans(s, size=26, color=WHITE, **kw):
    return Text(s, font=SANS, font_size=size, color=color, **kw)


def code_line(s, size=CODE_SIZE, color=WHITE):
    """A line of code whose vertical center does not depend on its glyphs.

    A '|' is prepended so every line has the same vertical extent, and is then
    dropped.  The returned group's reference point (the bar's left edge,
    vertically centered) is at the origin, so leading spaces indent properly.
    """
    ref = mono("|" + s, size, color)
    ref.move_to(ORIGIN, aligned_edge=LEFT)
    return VGroup(*ref.submobjects[1:])


# --------------------------------------------------------------------------
# Shared-memory objects
# --------------------------------------------------------------------------

class Padlock(VGroup):
    """The externally visible lock: free, or held by exactly one thread."""

    BODY_W = 0.7

    def __init__(self, name, **kw):
        super().__init__(**kw)
        self.name = name
        self.holder = None
        self.closed = False
        self.body = RoundedRectangle(corner_radius=0.08, width=self.BODY_W, height=0.55)
        self.body.set_stroke(FREE_COLOR, 3).set_fill(FREE_COLOR, 0.15)
        r = 0.2
        arc = Arc(radius=r, start_angle=0, angle=PI)
        legs = VGroup(Line(LEFT * r, LEFT * r + DOWN * 0.2),
                      Line(RIGHT * r, RIGHT * r + DOWN * 0.2))
        self.shackle = VGroup(arc, legs).set_stroke(FREE_COLOR, 6)
        self.shackle.next_to(self.body, UP, buff=-0.06)
        self.shackle.shift(UP * 0.2)  # start open
        hole = VGroup(Circle(radius=0.06), Triangle().scale(0.07).shift(DOWN * 0.08))
        hole.set_stroke(width=0).set_fill(BLACK, 1).move_to(self.body)
        self.keyhole = hole
        self.label = mono(name, 24).next_to(self.body, DOWN, buff=0.12)
        self.status = sans("free", 18, FREE_COLOR).next_to(self.label, DOWN, buff=0.08)
        reserve = sans("held by T4", 18).move_to(self.status).set_opacity(0)
        self.add(self.shackle, self.body, self.keyhole, self.label, self.status, reserve)

    @property
    def s(self):
        return self.body.width / self.BODY_W

    def _status(self, text, color):
        return sans(text, 18, color).scale(self.s).next_to(self.label, DOWN, buff=0.08 * self.s)

    def anim_close(self, color, holder_name):
        anims = []
        sh = self.shackle.animate.set_stroke(color)
        if not self.closed:
            sh = sh.shift(DOWN * 0.2 * self.s)
        anims.append(sh)
        anims.append(self.body.animate.set_stroke(color).set_fill(color, 0.6))
        anims.append(Transform(self.status, self._status(f"held by {holder_name}", color)))
        self.closed = True
        return anims

    def anim_open(self):
        anims = [self.shackle.animate.set_stroke(FREE_COLOR).shift(UP * 0.2 * self.s),
                 self.body.animate.set_stroke(FREE_COLOR).set_fill(FREE_COLOR, 0.15),
                 Transform(self.status, self._status("free", FREE_COLOR))]
        self.closed = False
        return anims

    def anchor(self):
        """Where tethers to threads attach."""
        return self.label.get_bottom() + DOWN * 0.35 * self.s


class DataCell(VGroup):
    SIZE = 0.85

    def __init__(self, name, value=0, **kw):
        super().__init__(**kw)
        self.name = name
        self.value = value
        self.racing = False
        self.box = Square(self.SIZE).set_stroke(WHITE, 3)
        self.name_t = mono(name, 24).next_to(self.box, UP, buff=0.1)
        self.val = self._val_text(value)
        self.race_label = sans("⚠ race", 18, BAD)
        self.add(self.box, self.name_t, self.val)

    def _val_text(self, v, color=WHITE):
        s = self.box.width / self.SIZE
        return mono(str(v), 34, color).scale(s).move_to(self.box)

    def anim_set(self, v):
        self.value = v
        return Transform(self.val, self._val_text(v))

    def anim_race(self, on):
        if on:
            self.race_label.next_to(self.box, DOWN, buff=0.1)
            return [self.box.animate.set_stroke(BAD, 6), FadeIn(self.race_label, scale=1.3)]
        return [self.box.animate.set_stroke(WHITE, 3), FadeOut(self.race_label)]


class Guard(VGroup):
    """Dashed frame showing which data a lock protects."""

    def __init__(self, lock, cells, **kw):
        super().__init__(**kw)
        self.lock, self.cells = lock, cells
        content = VGroup(lock, *cells).arrange(RIGHT, buff=0.6)
        rect = RoundedRectangle(corner_radius=0.2, width=content.width + 0.6,
                                height=content.height + 0.4).move_to(content)
        self.frame = DashedVMobject(rect, num_dashes=60).set_stroke(GREY_A, 2)
        names = ", ".join(c.name for c in cells)
        self.caption = sans(f"{lock.name} protects {names}", 18, GREY_A)
        self.caption.next_to(self.frame, UP, buff=0.08)
        self.add(self.frame, self.caption, content)


# --------------------------------------------------------------------------
# Code operations executed by threads
# --------------------------------------------------------------------------

class Op:
    """One line of thread code.  ``run`` returns (effect anims, follow-up anims)."""
    comment = False
    var = None

    def __init__(self, text, color=None):
        self.text, self.color = text, color

    def run(self, sc, th):
        return [], []


class Comment(Op):
    comment = True

    def __init__(self, text, color=GREY_B):
        super().__init__(text, color)


class Acquire(Op):
    def __init__(self, lock, color=None):
        super().__init__(f"acquire({lock});", color)
        self.lock = lock

    def run(self, sc, th):
        L = sc.locks[self.lock]
        if L.holder is None:
            return sc.take_lock(th, L), []
        th.next_pc = th.pc  # stay here: blocked
        if th.waiting_on is L:
            return [Wiggle(th.wait_badge, scale_value=1.15)], []
        return sc.block(th, L), []


class Release(Op):
    def __init__(self, lock, color=None):
        super().__init__(f"release({lock});", color)
        self.lock = lock

    def run(self, sc, th):
        return sc.release_lock(th, sc.locks[self.lock]), []


class Load(Op):
    def __init__(self, var, color=None):
        super().__init__(f"tmp = {var};", color)
        self.var = var

    def run(self, sc, th):
        cell = sc.cells[self.var]
        fly = cell.val.copy()
        th.tmp = cell.value
        return ([fly.animate.scale(0.6).move_to(th.tmp_val).set_color(th.color)],
                [FadeOut(fly), th.anim_tmp(th.tmp)])


class AddOne(Op):
    def __init__(self, color=None):
        super().__init__("tmp = tmp + 1;", color)

    def run(self, sc, th):
        th.tmp += 1
        return [th.anim_tmp(th.tmp), Indicate(th.tmp_val, color=th.color)], []


class Store(Op):
    def __init__(self, var, color=None):
        super().__init__(f"{var} = tmp;", color)
        self.var = var

    def run(self, sc, th):
        cell = sc.cells[self.var]
        fly = th.tmp_val.copy()
        return ([fly.animate.scale(1.6).move_to(cell.val)],
                [FadeOut(fly), cell.anim_set(th.tmp), Indicate(cell.box, color=th.color)])


class Inc(Op):
    """x = x + 1, shown as a single step (used where the race is not the point)."""

    def __init__(self, var, color=None):
        super().__init__(f"{var} = {var} + 1;", color)
        self.var = var

    def run(self, sc, th):
        cell = sc.cells[self.var]
        return [cell.anim_set(cell.value + 1), Indicate(cell.box, color=th.color)], []


class If(Op):
    """if (cond) falls through to the next line, else jumps to ``else_pc``."""

    def __init__(self, text, var, pred, else_pc, color=None):
        super().__init__(text, color)
        self.var, self.pred, self.else_pc = var, pred, else_pc

    def run(self, sc, th):
        val = self.pred(sc.cells[self.var].value)
        if not val:
            th.next_pc = self.else_pc
        tag = sans("true" if val else "false", 18, GREEN_B if val else GREY_B)
        tag.next_to(th.lines[th.pc], RIGHT, buff=0.2)
        return [FadeIn(tag, shift=LEFT * 0.1)], [FadeOut(tag)]


class Return(Op):
    def __init__(self, text="return;", color=None):
        super().__init__(text, color)

    def run(self, sc, th):
        th.next_pc = len(th.ops)
        return [], []


# --------------------------------------------------------------------------
# Threads
# --------------------------------------------------------------------------

class ThreadPanel(VGroup):
    def __init__(self, idx, ops, width=3.2, show_tmp=True, shade=True, name=None,
                 code_size=CODE_SIZE, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.color = THREAD_COLORS[idx]
        self.name = name or f"T{idx + 1}"
        self.ops = ops
        self.tmp = None
        self.waiting_on = None
        self.holding = set()
        self.in_cs = False
        self.done = False
        self.vars = {op.var for op in ops if op.var}
        self.lh = lh = LINE_H * code_size / CODE_SIZE

        # code
        self.anchor_pt = Dot(ORIGIN, radius=0.001).set_opacity(0)
        self.lines = VGroup()
        self.line_colors = []
        for i, op in enumerate(ops):
            c = op.color or WHITE
            self.line_colors.append(c)
            self.lines.add(code_line(op.text, code_size, c).shift(DOWN * i * lh))
        n = len(ops)

        self.header = sans(f"Thread {self.name}", 22, self.color)
        self.header.move_to(UP * 0.5 + LEFT * 0.3, aligned_edge=LEFT)

        content = VGroup(self.header, self.lines)
        if show_tmp:
            lab = mono("tmp =", 20, GREY_B).move_to(DOWN * (n * lh + 0.05), aligned_edge=LEFT)
            self.tmp_val = mono("?", 22, GREY_B).next_to(lab, RIGHT, buff=0.15)
            self.tmp_row = VGroup(lab, self.tmp_val)
            content.add(self.tmp_row)
        else:
            bottom = Dot(DOWN * ((n - 1) * lh + 0.15), radius=0.001).set_opacity(0)
            content.add(bottom)

        self.frame = RoundedRectangle(corner_radius=0.15, width=width, height=content.height + 0.35)
        self.frame.move_to([-0.45 + width / 2, content.get_y(), 0])
        self.frame.set_stroke(self.color, 2).set_fill(self.color, 0)

        # critical section bounds: inside iff lo < pc <= hi
        acq = [i for i, o in enumerate(ops) if isinstance(o, Acquire)]
        rel = [i for i, o in enumerate(ops) if isinstance(o, Release)]
        if acq and rel:
            self.cs = (acq[0], rel[-1])
            sh = (acq[0] + 1, rel[-1] - 1)
        else:
            acc = [i for i, o in enumerate(ops) if o.var]
            self.cs = (acc[0], acc[-1]) if acc else (n, n)
            sh = (acc[0], acc[-1]) if acc else None
        self.shade = None
        if sh and sh[0] <= sh[1]:
            self.shade = Rectangle(width=width - 0.2, height=(sh[1] - sh[0] + 1) * lh)
            self.shade.set_stroke(width=0).set_fill(SHADE_COLOR, 0.22 if shade else 0)
            self.shade.move_to([self.frame.get_x(), -(sh[0] + sh[1]) / 2 * lh, 0])

        self.pointer = Triangle().rotate(-PI / 2).scale(0.09).set_stroke(width=0)
        self.pointer.set_fill(self.color, 1)

        self.wait_badge = sans("waiting", 18, BAD)
        self.done_badge = sans("done", 18, GREY_B)
        for b in (self.wait_badge, self.done_badge):
            b.move_to(self.frame.get_corner(UR) + LEFT * 0.15 + DOWN * 0.12, aligned_edge=UR)

        self.add(self.frame)
        if self.shade is not None:
            self.add(self.shade)
        self.add(self.anchor_pt, content)
        self.pc = self._skip(0)
        self.pointer.move_to(self.pointer_pos(self.pc))
        self.add(self.pointer)
        # badges are positioned with the panel but shown only on demand
        self.badges = VGroup(self.wait_badge, self.done_badge)

    # program counter -----------------------------------------------------
    def _skip(self, pc):
        while pc < len(self.ops) and self.ops[pc].comment:
            pc += 1
        return pc

    def pointer_pos(self, pc):
        a = self.anchor_pt.get_center()
        return a + LEFT * 0.2 + DOWN * pc * self.lh

    def inside(self):
        lo, hi = self.cs
        return not self.done and lo < self.pc <= hi

    # animations -------------------------------------------------------------
    def anim_tmp(self, v):
        new = mono(str(v), 22, self.color).move_to(self.tmp_val, aligned_edge=LEFT)
        return Transform(self.tmp_val, new)

    def anim_glow(self, on):
        return self.frame.animate.set_stroke(width=6 if on else 2).set_fill(self.color, 0.15 if on else 0)


# --------------------------------------------------------------------------
# Scene base class
# --------------------------------------------------------------------------

class LockScene(Scene):
    SHARED_Y = 2.0
    PANEL_TOP = 0.3

    def setup(self):
        self.threads = []
        self.locks = {}
        self.cells = {}
        self.groups = {}
        self.tethers = {}
        self.waitlines = {}
        self.caption_mob = None

    # titles & captions --------------------------------------------------------
    def title(self, text):
        t = sans(text, 32, WHITE, weight=BOLD).to_edge(UP, buff=0.2)
        self.title_mob = t
        self.play(FadeIn(t, shift=DOWN * 0.2))
        return t

    def say(self, text, wait=None, size=24):
        new = sans(text, size, line_spacing=0.8)
        if new.width > 13.4:
            new.scale_to_fit_width(13.4)
        new.to_edge(DOWN, buff=0.2)
        anims = [FadeIn(new, shift=UP * 0.1)]
        if self.caption_mob is not None:
            anims.append(FadeOut(self.caption_mob))
        self.play(*anims, run_time=0.5)
        self.caption_mob = new
        self.wait(wait if wait is not None else 0.8 + 0.035 * len(text))

    # world construction -------------------------------------------------------
    def build(self, groups, threads, panel_width=None, show_tmp=True, shade=True,
              shared_y=None, panel_top=None, animate=True):
        """groups: [(lock_name or None, [(var, value), ...]), ...]
        threads: [list of Op, ...]"""
        shared_y = self.SHARED_Y if shared_y is None else shared_y
        panel_top = self.PANEL_TOP if panel_top is None else panel_top
        gmobs = []
        for lname, cells in groups:
            cms = [DataCell(n, v) for n, v in cells]
            for c in cms:
                self.cells[c.name] = c
            if lname:
                L = Padlock(lname)
                self.locks[lname] = L
                g = Guard(L, cms)
                self.groups[lname] = g
            else:
                g = VGroup(*cms).arrange(RIGHT, buff=0.6)
            gmobs.append(g)
        self.shared = VGroup(*gmobs).arrange(RIGHT, buff=1.4).move_to([0, shared_y, 0])

        n = len(threads)
        if panel_width is None:
            panel_width = min(3.8, (13.8 - 0.3 * (n - 1)) / n)
        code_size = CODE_SIZE if n <= 3 else CODE_SIZE - 2
        panels = [ThreadPanel(i, ops, width=panel_width, show_tmp=show_tmp, shade=shade,
                              code_size=code_size)
                  for i, ops in enumerate(threads)]
        self.threads = panels
        row = VGroup(*[VGroup(p, p.badges) for p in panels])
        row.arrange(RIGHT, buff=1.6 if n <= 2 else 0.3, aligned_edge=UP)
        row.move_to([0, 0, 0]).align_to([0, panel_top, 0], UP)
        if animate:
            self.play(FadeIn(self.shared), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.2) for p in panels], lag_ratio=0.2))
        else:
            self.add(self.shared, *panels)
        return panels

    # lock primitives ------------------------------------------------------------
    def take_lock(self, th, L):
        anims = []
        if th.waiting_on is not None:
            anims += self.unblock(th)
        L.holder = th
        th.holding.add(L)
        anims += L.anim_close(th.color, th.name)
        tether = Line(L.anchor(), th.frame.get_top(), color=th.color, stroke_width=4)
        self.tethers[(th, L)] = tether
        anims.append(Create(tether))
        return anims

    def release_lock(self, th, L):
        L.holder = None
        th.holding.discard(L)
        anims = L.anim_open()
        anims.append(Uncreate(self.tethers.pop((th, L))))
        return anims

    def block(self, th, L):
        th.waiting_on = L
        dl = DashedLine(L.anchor(), th.frame.get_top(), color=BAD, stroke_width=3, dash_length=0.12)
        self.waitlines[th] = dl
        return [Create(dl), FadeIn(th.wait_badge, scale=1.3), th.pointer.animate.set_fill(BAD)]

    def unblock(self, th):
        th.waiting_on = None
        return [FadeOut(self.waitlines.pop(th)), FadeOut(th.wait_badge),
                th.pointer.animate.set_fill(th.color)]

    # execution --------------------------------------------------------------------
    def step(self, *ths, rt=0.8):
        """Execute the next line of each given thread, concurrently."""
        effects, posts = [], []
        active = [th for th in ths if not th.done]
        for th in active:
            th.next_pc = th.pc + 1
            e, p = th.ops[th.pc].run(self, th)
            effects += e
            posts += p
            effects.append(th.lines[th.pc].animate.set_color(th.color))
        if effects:
            self.play(*effects, run_time=rt)
        for th in active:
            posts.append(th.lines[th.pc].animate.set_color(th.line_colors[th.pc]))
            new_pc = th._skip(th.next_pc)
            th.pc = new_pc
            if new_pc >= len(th.ops):
                th.done = True
                posts += [FadeOut(th.pointer), FadeIn(th.done_badge)]
            else:
                posts.append(th.pointer.animate.move_to(th.pointer_pos(new_pc)))
        posts += self.update_cs()
        if posts:
            self.play(*posts, run_time=0.4)

    def run(self, schedule, rt=0.8, pause=0.0):
        """schedule: sequence of thread indices (or tuples of indices = parallel)."""
        for item in schedule:
            idx = item if isinstance(item, (tuple, list)) else (item,)
            self.step(*[self.threads[i] for i in idx], rt=rt)
            if pause:
                self.wait(pause)

    def update_cs(self):
        anims = []
        for th in self.threads:
            inside = th.inside()
            if inside != th.in_cs:
                th.in_cs = inside
                anims.append(th.anim_glow(inside))
        for name, cell in self.cells.items():
            n = sum(1 for th in self.threads if th.in_cs and name in th.vars)
            racing = n >= 2
            if racing != cell.racing:
                cell.racing = racing
                anims += cell.anim_race(racing)
        return anims

    # results ----------------------------------------------------------------------
    def verdict(self, var, expected, side=RIGHT, anchor=None):
        cell = self.cells[var]
        ok = cell.value == expected
        color = GREEN_C if ok else BAD
        lines = VGroup(
            sans(f"expected {var} = {expected}", 22, GREY_A),
            sans(f"actual   {var} = {cell.value}", 22, color),
            sans("✓ correct" if ok else "✗ lost update", 24, color, weight=BOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        anchor = anchor if anchor is not None else cell
        lines.next_to(anchor, side, buff=0.6)
        self.play(FadeIn(lines, shift=-side * 0.2),
                  cell.box.animate.set_stroke(color, 6))
        return lines
