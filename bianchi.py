from manim import *

class RindlerHorizonScene(Scene):
    def construct(self):
        # Horizon as a vertical line (x=0) and label
        horizon_line = Line(start=DOWN*1.5, end=UP*1.5, color=YELLOW)
        horizon_label = Tex(r"Horizon ($\ell = 0$)", color=YELLOW).next_to(horizon_line, LEFT, buff=0.2)
        # Proper distance arrow for \ell coordinate
        obs_position = RIGHT * 2.0  # observer at x = 2 (some proper distance)
        ell_arrow = Arrow(start=horizon_line.get_right(), end=obs_position, stroke_width=5, color=BLUE)
        ell_label = MathTex(r"\ell", color=BLUE).next_to(ell_arrow, UP, buff=0.1)
        # Observer represented as a small dot with label
        observer_dot = Dot(point=obs_position, color=WHITE)
        observer_label = Tex("Observer", color=WHITE).next_to(observer_dot, UP, buff=0.1)
        # Metric text
        metric = MathTex(r"ds^2 = -(\kappa\,\ell)^2 dt^2 + d\ell^2 + r_S^2 d\Omega^2")
        metric.scale(0.8).to_edge(UP)  # scale down a bit and place at top
        # Add all elements to the scene
        self.add(horizon_line, horizon_label, ell_arrow, ell_label, observer_dot, observer_label, metric)

class HorizonDetectorScene(Scene):
    def construct(self):
        # Horizon and observer as context (reuse style from Scene 1)
        horizon_line = Line(start=DOWN*1.2, end=UP*1.2, color=YELLOW)
        horizon_label = Tex(r"$\ell=0$ Horizon", color=YELLOW).scale(0.8).next_to(horizon_line, LEFT, buff=0.2)
        observer_dot = Dot(point=RIGHT*2.0, color=WHITE)
        detector_label = Tex("Two-level detector").scale(0.7).next_to(observer_dot, UP, buff=0.1)
        # Two-level energy diagram: two horizontal lines for ground and excited states
        level_gap = 0.6
        ground_level = Line(LEFT*0.5, RIGHT*0.5, color=WHITE).move_to(observer_dot.get_center() + UP*0.3)
        excited_level = Line(LEFT*0.5, RIGHT*0.5, color=WHITE).next_to(ground_level, UP, buff=level_gap)
        # Labels |g> and |e>
        ground_label = MathTex(r"|g\rangle").scale(0.7).next_to(ground_level, LEFT, buff=0.1)
        excited_label = MathTex(r"|e\rangle").scale(0.7).next_to(excited_level, LEFT, buff=0.1)
        # Transition arrows between levels
        up_arrow = Arrow(start=ground_level.get_right(), end=excited_level.get_right(), buff=0.1, color=GREEN)
        down_arrow = Arrow(start=excited_level.get_right(), end=ground_level.get_right(), buff=0.1, color=RED)
        up_label = MathTex(r"\Gamma_{+}").scale(0.7).next_to(up_arrow, RIGHT, buff=0.1)
        down_label = MathTex(r"\Gamma_{-}").scale(0.7).next_to(down_arrow, RIGHT, buff=0.1)
        # Energy gap bracket with ΔE
        gap_brace = Brace(Line(excited_level.get_right(), ground_level.get_right()), RIGHT)
        gap_label = MathTex(r"\Delta E").scale(0.7).next_to(gap_brace, RIGHT, buff=0.1)
        # Acceleration and Temperature formulas
        a_T_formulas = MathTex(r"a \;=\; \frac{1}{\ell}, \qquad T \;=\; \frac{\hbar\,a}{2\pi}")
        a_T_formulas.scale(0.8).to_corner(UL)
        # Transition rate ratio formula
        ratio_formula = MathTex(r"\frac{\Gamma_{+}}{\Gamma_{-}} \;=\; e^{-\Delta E / T}").scale(0.8)
        ratio_formula.next_to(a_T_formulas, DOWN, aligned_edge=LEFT, buff=0.3)
        # Boltzmann factor plot: axes and exponential curve
        axes = Axes(
            x_range=[0, 4, 1],
            y_range=[0, 1.1, 1],
            x_length=3,
            y_length=2,
            axis_config={"stroke_color": GREY}
        )

        axes_labels = axes.get_axis_labels(x_label="\\Delta E", y_label="e^{-\\Delta E/T}")
        # Exponential decay curve on the axes
        decay_curve = axes.plot(lambda x: np.exp(-x), color=BLUE)
        axes_group = VGroup(axes, axes_labels, decay_curve).scale(0.6)
        axes_group.to_corner(DR, buff=0.5)
        # Add all elements
        self.add(horizon_line, horizon_label, observer_dot, detector_label,
                 ground_level, excited_level, ground_label, excited_label,
                 up_arrow, down_arrow, up_label, down_label, gap_brace, gap_label,
                 a_T_formulas, ratio_formula, axes_group)

class SurfaceFacetsScene(Scene):
    def construct(self):
        # Represent the horizon surface as a grid of small square facets
        facets = VGroup()
        rows, cols = 2, 3
        for i in range(rows):
            for j in range(cols):
                square = Square(side_length=0.5, stroke_color=WHITE, fill_color=GREY, fill_opacity=0.1)
                square.move_to(np.array([j*0.55, i*0.55, 0]))  # slight gap between squares
                facets.add(square)
        facets_center = facets.get_center()
        facets.shift(LEFT*3 + DOWN*facets_center[1]*0.5)  # move facets to left side
        # Label each facet with a spin value j_{i}
        labels = VGroup()
        for k, sq in enumerate(facets):
            j_label = MathTex(f"j_{{{k+1}}}", color=WHITE).scale(0.7)
            j_label.move_to(sq.get_center())
            labels.add(j_label)
        # Equations for boost Hamiltonian and facet entropy
        boost_eq = MathTex(r"H_f \;=\; \hbar\,\gamma\, j_f\, a")
        entropy_eq = MathTex(r"\delta S_f \;=\; 2\pi\, \gamma\, j_f")
        equations = VGroup(boost_eq, entropy_eq).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        equations.to_corner(UR)
        # Add elements
        self.add(facets, labels, equations)


class EntropyDerivationScene(Scene):
    def construct(self):
        # Left column: Clausius relation approach
        title_left = Tex(r"\textbf{Clausius relation:}").scale(0.8)
        clausius_eq = MathTex(r"\delta S = \frac{\delta E}{T}")
        # Derivation steps for S using Clausius (aligned equations)
        clausius_deriv = MathTex(r"""
            \begin{aligned}
            S &= 2\pi\,\gamma \sum_f j_f \\
              &= 2\pi\,\gamma \frac{A}{8\pi G \hbar \gamma} \\
              &= \frac{A}{4\,G\,\hbar}\,. 
            \end{aligned}
        """)
        clausius_group = VGroup(title_left, clausius_eq, clausius_deriv).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        clausius_group.to_corner(UL)
        # Right column: Partition function approach
        title_right = Tex(r"\textbf{Partition function:}").scale(0.8)
        Z_formula = MathTex(
            r"Z(\beta) = \exp\left[-\,\frac{1}{8 \pi G \hbar} \sum_f A_f\,(\beta a - 2\pi)\right]"
        )
        thermo_ids = MathTex(r"""
            \begin{aligned}
            E(\beta) &= -\,\frac{\partial}{\partial \beta}\ln Z(\beta), \\
            S(\beta) &= \ln Z(\beta) + \beta\,E(\beta)\,.
            \end{aligned}
        """)
        results = MathTex(r"""
            \begin{aligned}
            E &= \frac{a\,A}{8\pi G \hbar}, \\
            S &= \frac{A}{4\,G\,\hbar}\,. 
            \end{aligned}
        """)
        partfn_group = VGroup(title_right, Z_formula, thermo_ids, results).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        partfn_group.to_corner(UR)
        # Add both groups
        self.add(clausius_group, partfn_group)
