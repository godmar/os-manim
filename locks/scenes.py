"""
Lock visualizations.  Render one scene with, e.g.

    manim -qh scenes.py S3_MutualExclusion

or all of them with ./render.sh.
"""
from lockviz import *


def incr(var="x", lock=None):
    """tmp = x; tmp = tmp + 1; x = tmp; -- optionally wrapped in acquire/release."""
    body = [Load(var), AddOne(), Store(var)]
    if lock:
        return [Acquire(lock), *body, Release(lock)]
    return body


# ---------------------------------------------------------------------------
class S1_RaceCondition(LockScene):
    """Why we need mutual exclusion: a lost update."""

    def construct(self):
        self.title("1 · The Critical Section Problem")
        T1, T2 = self.build([(None, [("x", 0)])], [incr(), incr()], shade=False)
        self.say("Two threads each add 1 to a shared variable x.")
        self.say("x = x + 1 is really three steps: load into a private tmp, add, store back.")
        self.say("The scheduler may interleave these steps arbitrarily. For instance:", wait=1)

        self.step(T1)
        self.step(T2)
        self.say("Both threads have now read x = 0 ...", wait=1)
        self.step(T1)
        self.step(T2)
        self.step(T1)
        self.step(T2)
        self.verdict("x", 2)
        self.say("T2 overwrote T1's update.  The result depends on timing: a race condition.")

        shades = [th.shade for th in self.threads]
        labels = [sans("critical section", 16, YELLOW_C)
                  .next_to(s, DOWN, buff=0.04).align_to(s, RIGHT).shift(LEFT * 0.08) for s in shades]
        self.play(*[s.animate.set_fill(opacity=0.22) for s in shades], *[FadeIn(l) for l in labels])
        self.say("Code that accesses shared data is a critical section.")
        self.say("Requirement (mutual exclusion): at most one thread may be\n"
                 "inside a critical section for the same data at any time.", wait=3)


# ---------------------------------------------------------------------------
class S2_LockAbstraction(LockScene):
    """The lock as an abstract data type, and the lock/data convention."""

    def construct(self):
        self.title("2 · Locks: the Abstraction")
        L = Padlock("L").scale(1.6).move_to([-4.2, 1.0, 0])
        self.locks["L"] = L
        self.play(FadeIn(L))

        api = VGroup(
            VGroup(mono("acquire(L)", 26, YELLOW_C),
                   sans("wait until L is free, then take it", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.1),
            VGroup(mono("release(L)", 26, YELLOW_C),
                   sans("give L back (only the holder may do this)", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.1),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([2.2, 1.6, 0])
        self.say("A lock is an object with two operations.", wait=0.5)
        self.play(FadeIn(api[0], shift=LEFT * 0.2))
        self.play(FadeIn(api[1], shift=LEFT * 0.2))
        self.say("At any time, a lock is either free or held by exactly one thread.")

        # tiny thread tokens demonstrate the semantics
        def chip(i):
            c = Circle(radius=0.32).set_stroke(THREAD_COLORS[i], 3).set_fill(THREAD_COLORS[i], 0.3)
            return VGroup(c, sans(f"T{i + 1}", 20)).move_to([-5.2 + 2.0 * i, -1.4, 0])

        t1, t2 = chip(0), chip(1)
        t1.color, t1.name = THREAD_COLORS[0], "T1"
        t2.color, t2.name = THREAD_COLORS[1], "T2"
        self.play(FadeIn(t1), FadeIn(t2))

        def tether(t, color, dashed=False):
            cls = DashedLine if dashed else Line
            return cls(L.anchor(), t.get_top(), color=color, stroke_width=4 if not dashed else 3)

        a1 = mono("acquire(L)", 20, THREAD_COLORS[0]).next_to(t1, DOWN, buff=0.15)
        self.play(FadeIn(a1))
        line1 = tether(t1, THREAD_COLORS[0])
        self.play(*L.anim_close(THREAD_COLORS[0], "T1"), Create(line1))
        self.say("T1 acquires L.  L is now held by T1.", wait=1)

        a2 = mono("acquire(L)", 20, THREAD_COLORS[1]).next_to(t2, DOWN, buff=0.15)
        w2 = tether(t2, BAD, dashed=True)
        wl = sans("waiting", 18, BAD).next_to(t2, UP, buff=0.1).shift(RIGHT * 0.6)
        self.play(FadeIn(a2), Create(w2), FadeIn(wl))
        self.say("T2 tries to acquire L while T1 holds it: T2 must wait.")

        r1 = mono("release(L)", 20, THREAD_COLORS[0]).move_to(a1)
        self.play(FadeOut(a1), FadeIn(r1))
        self.play(*L.anim_open(), Uncreate(line1))
        line2 = tether(t2, THREAD_COLORS[1])
        self.play(*L.anim_close(THREAD_COLORS[1], "T2"), FadeOut(w2), FadeOut(wl), Create(line2))
        self.say("When T1 releases L, a waiting thread can acquire it.")
        r2 = mono("release(L)", 20, THREAD_COLORS[1]).move_to(a2)
        self.play(FadeOut(a2), FadeIn(r2))
        self.play(*L.anim_open(), Uncreate(line2))
        self.play(FadeOut(VGroup(t1, t2, r1, r2)))

        # the protects relation
        x = DataCell("x", 0)
        self.say("Note: the lock knows nothing about the data it protects.", wait=1.5)
        self.play(L.animate.scale(1 / 1.6).move_to([-4.8, 0.9, 0]), FadeOut(api))
        x.move_to([-3.4, 0.9, 0])
        self.play(FadeIn(x))
        rect = RoundedRectangle(corner_radius=0.2, width=3.2, height=2.2).move_to([-4.1, 0.85, 0])
        frame = DashedVMobject(rect, num_dashes=60).set_stroke(GREY_A, 2)
        cap = sans("L protects x", 18, GREY_A).next_to(frame, UP, buff=0.08)
        self.play(Create(frame), FadeIn(cap))
        rule = VGroup(
            sans("The association is a programmer convention:", 24),
            sans("access x only while holding L.", 28, YELLOW_C, weight=BOLD),
            sans("Every thread, every access, every time.", 22, GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([2.6, 1.0, 0])
        for r in rule:
            self.play(FadeIn(r, shift=LEFT * 0.2))
        self.say("Nothing enforces it -- that is why the frame is dashed.", wait=2)
        posix = sans("In POSIX threads:  pthread_mutex_t  ·  pthread_mutex_lock()  ·  pthread_mutex_unlock()",
                     20, GREY_B).move_to([0, -1.6, 0])
        self.play(FadeIn(posix))
        self.wait(2.5)


# ---------------------------------------------------------------------------
class S3_MutualExclusion(LockScene):
    """Solving the critical section problem with a lock."""

    def construct(self):
        self.title("3 · Mutual Exclusion with a Lock")
        T1, T2 = self.build([("L", [("x", 0)])], [incr("x", "L"), incr("x", "L")])
        self.say("Now each thread acquires L before its critical section and releases it after.")
        self.step(T1)
        self.say("T1 holds L and enters its critical section.", wait=1)
        self.step(T1)
        self.step(T2)
        self.say("T2 tries to acquire L, but T1 holds it: T2 waits.")
        self.step(T1)
        self.step(T1)
        self.say("Meanwhile, T1 finishes its update undisturbed.", wait=1)
        self.step(T1)
        self.say("T1 releases L ...", wait=0.5)
        self.step(T2)
        self.say("... and T2 can acquire it.  T2 now reads the updated x.", wait=1)
        self.run([1, 1, 1, 1], rt=0.6)
        self.verdict("x", 2)
        self.say("The critical sections cannot overlap: mutual exclusion.", wait=3)


# ---------------------------------------------------------------------------
class S4_ManyThreads(LockScene):
    """Several threads contending for one lock."""

    def construct(self):
        self.title("4 · Many Threads, One Lock")
        T = self.build([("L", [("x", 0)])], [incr("x", "L") for _ in range(4)])
        self.say("Four threads, one lock.")
        self.run([0])
        self.run([(1, 2, 3)])
        self.say("T1 got L first; T2, T3 and T4 all have to wait.")
        self.run([0, 0, 0], rt=0.6)
        self.run([0])
        self.say("When L is released, ONE of the waiting threads gets it.\n"
                 "Which one is not specified by the abstraction -- here, T3.", wait=2)
        self.run([(2, 1, 3)])
        self.run([2, 2, 2, 2], rt=0.5)
        self.run([(3, 1)])
        self.say("Waiting threads keep waiting until the lock becomes free.", wait=0.5)
        self.run([3, 3, 3, 3], rt=0.5)
        self.run([1, 1, 1, 1, 1], rt=0.5)
        self.verdict("x", 4)
        self.say("However many threads contend, at most one is inside its critical section.", wait=3)


# ---------------------------------------------------------------------------
class S5_ManyLocks(LockScene):
    """Different locks for different data allow parallelism."""

    def construct(self):
        self.title("5 · Multiple Locks, Multiple Data")
        T1, T2, T3 = self.build([("La", [("a", 0)]), ("Lb", [("b", 0)])],
                                [incr("a", "La"), incr("b", "Lb"), incr("a", "La")])
        self.say("Each piece of data gets its own lock: La protects a, Lb protects b.")
        self.run([(0, 1)])
        self.say("T1 and T2 hold different locks, so their critical sections\n"
                 "may run at the same time -- they touch different data.")
        self.run([2])
        self.say("T3 needs a, so it must wait for La -- held by T1.")
        self.run([(0, 1), (0, 1), (0, 1)], rt=0.7)
        self.run([(0, 1)])
        self.run([2])
        self.say("T1 released La; now T3 may update a.", wait=1)
        self.run([2, 2, 2, 2], rt=0.6)
        self.verdict("a", 2, side=LEFT, anchor=self.groups["La"])
        self.verdict("b", 1, side=RIGHT, anchor=self.groups["Lb"])
        self.say("Separate locks: mutual exclusion where needed, parallelism where possible.", wait=3)


# ---------------------------------------------------------------------------
class S6_ForgotLock(LockScene):
    """Risk: a thread accesses protected data without the lock."""

    def construct(self):
        self.title("6 · Risk: Forgetting to Acquire the Lock")
        buggy = [Comment("// no acquire!", BAD), *incr("x"), Comment("// no release!", BAD)]
        T1, T2 = self.build([("L", [("x", 0)])], [incr("x", "L"), buggy])
        self.say("T1 follows the rule.  T2's programmer forgot to acquire L.")
        self.run([0, 0])
        self.say("T1 holds L ...", wait=0.5)
        self.run([1])
        self.say("... but nothing stops T2 from reading x anyway!\nLocks are advisory -- they only work if everyone uses them.")
        self.run([0, 1, 1, 0, 0])
        self.verdict("x", 2)
        self.say("Data race: concurrent accesses to x, at least one a write,\n"
                 "without consistently holding the lock that protects x.", wait=3)


# ---------------------------------------------------------------------------
class S7_WrongLock(LockScene):
    """Risk: a thread holds a lock, but not the one that protects the data."""

    def construct(self):
        self.title("7 · Risk: Acquiring the Wrong Lock")
        buggy = [Acquire("Lb", BAD), Load("a"), AddOne(), Store("a"), Release("Lb", BAD)]
        T1, T2 = self.build([("La", [("a", 0)]), ("Lb", [("b", 0)])],
                            [incr("a", "La"), buggy])
        self.say("La protects a.  But T2 acquires Lb before updating a.")
        self.run([(0, 1)])
        self.say("Both threads hold a lock -- just not the same one.\nNeither has to wait.")
        self.run([0, 1, 0, 1, 0, 1])
        self.verdict("a", 2, side=LEFT, anchor=self.groups["La"])
        self.say("Holding *a* lock is not enough: every access to a must hold La,\n"
                 "the lock associated with a.", wait=3)


# ---------------------------------------------------------------------------
class S8_ForgotRelease(LockScene):
    """Risk: a code path that never releases the lock."""

    def construct(self):
        self.title("8 · Risk: Forgetting to Release the Lock")

        def code():
            return [Acquire("L"),
                    If("if (x >= 10)", "x", lambda v: v >= 10, else_pc=3),
                    Return("    return;", BAD),
                    Inc("x"),
                    Release("L")]

        T1, T2, T3 = self.build([("L", [("x", 9)])], [code(), code(), code()], show_tmp=False)
        self.say("Increment x, but never beyond 10.  Note the early return ...")
        self.run([0, 0, 0, 0], rt=0.7)
        self.say("T1 took the normal path: x is now 10, and L was released.", wait=1)
        self.run([1, 1])
        self.say("T2 sees x >= 10 and returns early -- without releasing L!", wait=1)
        self.run([1])
        self.say("T2 is done, yet L is still held by T2.", wait=1.5)
        self.run([2])
        self.say("T3 tries to acquire L ...", wait=0.5)
        self.run([2])
        self.run([2])
        forever = sans("... forever", 24, BAD, weight=BOLD).next_to(T3.frame, DOWN, buff=0.15)
        self.play(FadeIn(forever, shift=DOWN * 0.1), Indicate(T3.wait_badge, color=BAD))
        self.say("No one will ever release L: T3, and every later thread, waits forever.\n"
                 "The program hangs (deadlock).", wait=2.5)
        self.say("Fix: release the lock on every path out of the critical section.", wait=3)


# ---------------------------------------------------------------------------
class S9_LockInternals(LockScene):
    """Zoom into the lock: one possible implementation of the abstraction."""

    PH = 0.285  # pseudo-code line height
    PSEUDO = [
        "acquire(L):",
        "  if L.holder == none:",
        "    L.holder = me",
        "  else:",
        "    append me to L.waiters",
        "    block (sleep)",
        "release(L):",
        "  if L.waiters is not empty:",
        "    L.holder = pop L.waiters",
        "    wake up L.holder",
        "  else:",
        "    L.holder = none",
    ]

    def construct(self):
        self.title("9 · Inside the Lock")
        code = lambda: [Acquire("L"), Inc("x"), Release("L")]
        T1, T2, T3 = self.build([("L", [("x", 0)])], [code(), code(), code()],
                                show_tmp=False, shared_y=1.6, panel_top=-0.95,
                                panel_width=3.6)
        L = self.locks["L"]
        self.play(self.groups["L"].animate.move_to([-4.9, 1.55, 0]))
        self.say("So far we have treated the lock as a black box with two operations.", wait=1)

        # ---- zoom
        inset = RoundedRectangle(corner_radius=0.2, width=8.9, height=3.95)
        inset.move_to([2.15, 1.15, 0]).set_stroke(GREY_A, 2).set_fill(BLACK, 1)
        src = SurroundingRectangle(VGroup(L.shackle, L.body), buff=0.08).set_stroke(GREY_A, 2)
        zl = VGroup(Line(src.get_corner(UR), inset.get_corner(UL)),
                    Line(src.get_corner(DR), inset.get_corner(DL))).set_stroke(GREY_B, 1.5)
        # the inset sits above tethers, which may pass behind it
        inset.set_z_index(1)
        zl.set_z_index(1)
        self.play(Create(src))
        self.play(TransformFromCopy(src, inset), Create(zl), run_time=1.2)
        head = sans("inside L — one possible implementation", 18, GREY_B)
        head.move_to(inset.get_corner(UL) + RIGHT * 0.25 + DOWN * 0.25, aligned_edge=UL)

        # fields
        fx = inset.get_left()[0] + 0.35
        h_lab = mono("holder:", 22, GREY_A).move_to([fx, 2.05, 0], aligned_edge=LEFT)
        self.h_val = mono("none", 22, FREE_COLOR).next_to(h_lab, RIGHT, buff=0.2)
        w_lab = mono("waiters:", 22, GREY_A).move_to([fx, 1.25, 0], aligned_edge=LEFT)
        slots = VGroup(*[Square(0.55) for _ in range(3)]).arrange(RIGHT, buff=0)
        slots.set_stroke(GREY_B, 2).next_to(w_lab, DOWN, buff=0.2).align_to(w_lab, LEFT)
        self.slots = slots
        self.queue = []

        # pseudo code
        px = inset.get_left()[0] + 3.85
        ref = Dot(radius=0.001).set_opacity(0)
        self.pseudo = VGroup(*[code_line(s, 17, GREY_A).shift(DOWN * i * self.PH)
                               for i, s in enumerate(self.PSEUDO)])
        VGroup(ref, self.pseudo).move_to([px, 0.95, 0], aligned_edge=LEFT)
        self.pseudo_y0 = ref.get_y()
        self.pseudo_x = px
        self.hl = Rectangle(width=5.0, height=self.PH).set_stroke(width=0).set_fill(YELLOW_E, 0.35)
        self.hl.move_to([px - 0.08 + self.hl.width / 2, self.pseudo_y0, 0]).set_fill(opacity=0)

        self.play(FadeIn(head), FadeIn(VGroup(h_lab, self.h_val, w_lab, slots)),
                  FadeIn(self.pseudo))
        self.hl.set_z_index(2)
        for m in (head, h_lab, self.h_val, w_lab, slots, self.pseudo):
            m.set_z_index(3)
        self.add(self.hl)
        self.say("Inside, a lock may keep track of its holder and a queue of waiting threads.")
        self.say("(These fields are shared too! The implementation updates them atomically,\n"
                 "e.g. using atomic instructions or an internal spinlock.)", size=22)

        # ---- replay with internals
        self.acquire(T1)
        self.say("T1: L is free, so T1 becomes the holder.", wait=1)
        self.acquire(T2)
        self.say("T2: L is held, so T2 joins the waiting queue and goes to sleep.", wait=1)
        self.acquire(T3)
        self.step(T1)
        self.release(T1)
        self.say("Release hands L directly to the first waiter and wakes it up.", wait=1.5)
        self.step(T2, rt=0.6)
        self.release(T2)
        self.step(T3, rt=0.6)
        self.release(T3)
        self.say("With no waiters left, L becomes free again.", wait=1)
        self.play(self.hl.animate.set_fill(opacity=0))

        self.say("This is a detail of the implementation, hidden behind acquire/release.\n"
                 "Code that uses locks must not depend on it (e.g., on FIFO order).", wait=3)
        self.play(FadeOut(VGroup(inset, head, h_lab, self.h_val, w_lab, slots,
                                 self.pseudo, self.hl, zl, src)))
        self.say("From the outside, all you see is the abstraction: acquire and release.", wait=2.5)

    # helpers -------------------------------------------------------------------
    def highlight(self, i, j=None, rt=0.4):
        j = i if j is None else j
        h = (j - i + 1) * self.PH
        y = self.pseudo_y0 - (i + j) / 2 * self.PH
        self.play(self.hl.animate.set_fill(opacity=0.35).stretch_to_fit_height(h)
                  .move_to([self.pseudo_x - 0.08 + self.hl.width / 2, y, 0]), run_time=rt)

    def set_holder(self, th):
        name, color = (th.name, th.color) if th else ("none", FREE_COLOR)
        return Transform(self.h_val, mono(name, 22, color).move_to(self.h_val, aligned_edge=LEFT))

    def chip(self, th):
        c = Circle(radius=0.22).set_stroke(th.color, 3).set_fill(th.color, 0.4)
        ch = VGroup(c, sans(th.name, 15))
        ch.set_z_index(4)
        return ch

    def advance(self, th):
        th.pc = th._skip(th.pc + 1)
        return th.pointer.animate.move_to(th.pointer_pos(th.pc))

    def acquire(self, th):
        L = self.locks["L"]
        self.play(th.lines[th.pc].animate.set_color(th.color), run_time=0.3)
        self.highlight(0)
        self.highlight(1)
        if L.holder is None:
            self.highlight(2)
            self.play(self.set_holder(th), *self.take_lock(th, L))
        else:
            self.highlight(3, 4)
            ch = self.chip(th).move_to(th.frame.get_top())
            self.queue.append((th, ch))
            self.play(ch.animate.move_to(self.slots[len(self.queue) - 1]))
            self.highlight(5)
            self.play(*self.block(th, L))
        anims = [th.lines[th.cs[0]].animate.set_color(WHITE)]
        if th.waiting_on is None:
            anims.append(self.advance(th))
        anims += self.update_cs()
        self.play(*anims, run_time=0.4)

    def release(self, th):
        L = self.locks["L"]
        self.play(th.lines[th.pc].animate.set_color(th.color), run_time=0.3)
        self.highlight(6)
        self.highlight(7)
        anims = [Uncreate(self.tethers.pop((th, L)))]
        th.holding.discard(L)
        if self.queue:
            nxt, ch = self.queue.pop(0)
            self.highlight(8)
            moves = [c.animate.move_to(self.slots[k]) for k, (_, c) in enumerate(self.queue)]
            self.play(ch.animate.move_to(self.h_val), *moves)
            self.play(FadeOut(ch), self.set_holder(nxt), run_time=0.4)
            self.highlight(9)
            anims += self.take_lock(nxt, L)  # hand-off: unblocks nxt, recolors L
            nxt.lines[nxt.pc].set_color(WHITE)
            self.play(*anims)
            self.play(self.advance(nxt), run_time=0.4)
        else:
            self.highlight(10, 11)
            L.holder = None
            self.play(self.set_holder(None), *anims, *L.anim_open())
        th.pc = len(th.ops)
        th.done = True
        self.play(th.lines[-1].animate.set_color(WHITE), FadeOut(th.pointer),
                  FadeIn(th.done_badge), *self.update_cs(), run_time=0.4)
