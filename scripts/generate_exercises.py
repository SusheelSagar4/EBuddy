import csv
import json
import os
import pandas as pd

# Load existing exercises
existing_df = pd.read_csv('data/seed/kb/exercise.csv')

# Update source_url on existing exercises to repo path
existing_df['source_url'] = 'data/seed/kb/exercise.csv'
existing_records = existing_df.to_dict(orient='records')

new_exercises = []

# Helper to create clean exercise dict
def make_ex(ex_id, skill_id, prompt, opts, correct_letter, explanation, diff=2.0, est_min=3):
    return {
        'exercise_id': ex_id,
        'skill_id': skill_id,
        'module_id': None,
        'kind': 'mcq',
        'difficulty': diff,
        'prompt': prompt,
        'options': json.dumps(opts),
        'answer_key': json.dumps({'correct_option': correct_letter, 'explanation': explanation}),
        'rubric': 'Award full marks for selecting the correct option with analytical justification.',
        'est_minutes': est_min,
        'status': 'draft_for_review',
        'source_id': 'AI_DRAFT',
        'licence': 'CC-BY-4.0',
        'source_url': 'data/seed/kb/exercise.csv'
    }

# 1. CIRCUITS (SKILL_CIRCUIT_ANALYSIS) - need 7 more (004 to 010)
circuits = [
    (
        "EX_EE_CIRC_004", "SKILL_CIRCUIT_ANALYSIS",
        "A series RLC circuit has R = 10 Ohm, L = 0.1 H, and C = 100 uF. What is the resonant frequency (omega_0) of the circuit in rad/s?",
        {"A": "100 rad/s", "B": "316.2 rad/s", "C": "1000 rad/s", "D": "50 rad/s"},
        "B",
        "Resonant frequency omega_0 = 1 / sqrt(L * C) = 1 / sqrt(0.1 * 100e-6) = 1 / sqrt(1e-5) = 1 / 0.003162 = 316.23 rad/s.",
        2.0, 3
    ),
    (
        "EX_EE_CIRC_005", "SKILL_CIRCUIT_ANALYSIS",
        "In a two-port network, the impedance parameters Z11 and Z22 are measured with open-circuit conditions. If Z11 = 40 Ohm, Z12 = 10 Ohm, Z21 = 10 Ohm, and Z22 = 30 Ohm, what is the input impedance Zin looking into port 1 when port 2 is terminated with a 20 Ohm load?",
        {"A": "40.0 Ohm", "B": "38.0 Ohm", "C": "42.0 Ohm", "D": "50.0 Ohm"},
        "B",
        "Input impedance Zin = Z11 - (Z12 * Z21) / (Z22 + Z_L) = 40 - (10 * 10) / (30 + 20) = 40 - 100 / 50 = 40 - 2.0 = 38.0 Ohm.",
        3.0, 4
    ),
    (
        "EX_EE_CIRC_006", "SKILL_CIRCUIT_ANALYSIS",
        "A series RL circuit with R = 5 Ohm and L = 25 mH is connected across a 50 V DC supply at t = 0. What is the time constant tau of the circuit?",
        {"A": "5.0 ms", "B": "125.0 ms", "C": "0.2 ms", "D": "50.0 ms"},
        "A",
        "Time constant tau = L / R = 0.025 / 5 = 0.005 s = 5.0 ms.",
        1.5, 2
    ),
    (
        "EX_EE_CIRC_007", "SKILL_CIRCUIT_ANALYSIS",
        "According to Tellegen theorem, what is the sum of the products of branch voltages and branch currents for any lumped electrical network satisfying KCL and KVL?",
        {"A": "Equal to total active power only", "B": "Zero at all times", "C": "Equal to the reactive power", "D": "Dependent on the branch impedances"},
        "B",
        "Tellegen theorem states that for any lumped network, sum(v_k * i_k) = 0 for all branches k at any instant, independent of branch linearity or time-invariance.",
        2.0, 3
    ),
    (
        "EX_EE_CIRC_008", "SKILL_CIRCUIT_ANALYSIS",
        "A 3-phase balanced star-connected load has a line voltage of 415 V (rms). What is the phase voltage V_ph across each phase?",
        {"A": "415.0 V", "B": "239.6 V", "C": "718.8 V", "D": "207.5 V"},
        "B",
        "In a star (Y) connected system, V_ph = V_L / sqrt(3) = 415 / 1.732 = 239.6 V.",
        1.5, 2
    ),
    (
        "EX_EE_CIRC_009", "SKILL_CIRCUIT_ANALYSIS",
        "In maximum power transfer for an AC circuit, what condition must the load impedance Z_L = R_L + jX_L satisfy relative to the Thevenin impedance Z_th = R_th + jX_th?",
        {"A": "Z_L = Z_th", "B": "Z_L = Z_th* (complex conjugate)", "C": "R_L = R_th and X_L = X_th", "D": "Z_L = -Z_th"},
        "B",
        "For maximum average power transfer in AC networks, the load impedance must be the complex conjugate of the Thevenin internal impedance: Z_L = Z_th* (i.e. R_L = R_th and X_L = -X_th).",
        2.0, 3
    ),
    (
        "EX_EE_CIRC_010", "SKILL_CIRCUIT_ANALYSIS",
        "A capacitor C = 50 uF is charged to 100 V and then discharged through a resistor R = 20 kOhm. What is the initial discharge current at t = 0+?",
        {"A": "5.0 mA", "B": "2.0 mA", "C": "50.0 mA", "D": "0.5 mA"},
        "A",
        "At t = 0+, the capacitor maintains its voltage V = 100 V. The discharge current I(0+) = V / R = 100 / 20000 = 0.005 A = 5.0 mA.",
        1.5, 2
    )
]

# 2. MACHINES (SKILL_ELECTRIC_MACHINES) - need 7 more (004 to 010)
machines = [
    (
        "EX_EE_MACH_004", "SKILL_ELECTRIC_MACHINES",
        "In a DC shunt generator, why is residual magnetism in the field poles essential during startup?",
        {"A": "To suppress commutator sparking", "B": "To initiate self-excitation voltage buildup", "C": "To keep the speed constant", "D": "To prevent armature reaction"},
        "B",
        "Residual magnetism creates a small initial induced emf upon rotation, driving current through the field winding to build up the magnetic flux and terminal voltage.",
        2.0, 3
    ),
    (
        "EX_EE_MACH_005", "SKILL_ELECTRIC_MACHINES",
        "A 3-phase, 50 Hz, 6-pole synchronous generator runs at synchronous speed. What is its mechanical shaft speed in rpm?",
        {"A": "1500 rpm", "B": "1000 rpm", "C": "3000 rpm", "D": "750 rpm"},
        "B",
        "Synchronous speed N_s = (120 * f) / P = (120 * 50) / 6 = 6000 / 6 = 1000 rpm.",
        1.5, 2
    ),
    (
        "EX_EE_MACH_006", "SKILL_ELECTRIC_MACHINES",
        "What is the primary purpose of conducting the open-circuit (OC) test on a single-phase transformer?",
        {"A": "To determine copper loss and series winding resistance", "B": "To determine core (iron) loss and magnetizing branch parameters", "C": "To test the dielectric breakdown of oil", "D": "To evaluate short-circuit impedance"},
        "B",
        "In an OC test conducted at rated voltage, series current is very small so copper losses are negligible; total measured power represents core losses (hysteresis + eddy current), allowing extraction of R_c and X_m.",
        2.0, 3
    ),
    (
        "EX_EE_MACH_007", "SKILL_ELECTRIC_MACHINES",
        "In an induction motor, what happens to the rotor frequency f_r as the motor accelerates from standstill (s=1) to near synchronous speed (s=0.03)?",
        {"A": "Remains constant at 50 Hz", "B": "Decreases proportionally with slip from 50 Hz to 1.5 Hz", "C": "Increases above 50 Hz", "D": "Becomes zero at all non-zero slips"},
        "B",
        "Rotor induced emf frequency is f_r = s * f_supply. At standstill (s=1), f_r = 50 Hz. At s=0.03, f_r = 0.03 * 50 = 1.5 Hz.",
        2.0, 3
    ),
    (
        "EX_EE_MACH_008", "SKILL_ELECTRIC_MACHINES",
        "Why are transformer cores assembled using thin laminated silicon steel sheets rather than solid steel blocks?",
        {"A": "To increase mechanical rigidity", "B": "To minimize eddy current losses by restricting circulation paths", "C": "To decrease permeability", "D": "To avoid copper losses in the winding"},
        "B",
        "Laminating the core introduces insulation barriers that restrict eddy current loop paths, significantly reducing eddy current losses which vary with the square of lamination thickness (t^2).",
        2.0, 3
    ),
    (
        "EX_EE_MACH_009", "SKILL_ELECTRIC_MACHINES",
        "In a DC series motor, torque T is related to armature current I_a (before magnetic saturation) by:",
        {"A": "T proportional to I_a", "B": "T proportional to I_a^2", "C": "T proportional to 1 / I_a", "D": "T is independent of I_a"},
        "B",
        "In a series motor, field flux Phi is proportional to I_a (unsaturated). Torque T = k * Phi * I_a = k' * I_a^2. This gives the high starting torque characteristic.",
        2.0, 3
    ),
    (
        "EX_EE_MACH_010", "SKILL_ELECTRIC_MACHINES",
        "What is the function of damper windings in a synchronous machine?",
        {"A": "To supply field excitation during normal steady state", "B": "To damp hunting oscillations and provide starting torque as an induction motor", "C": "To correct armature reaction cross-magnetization", "D": "To prevent stator core saturation"},
        "B",
        "Damper windings embedded in pole faces develop induction torque during speed variations, damping rotor hunting oscillations and allowing self-starting as an induction motor.",
        2.5, 3
    )
]

# 3. POWER (SKILL_POWER_ELECTRONICS & SKILL_POWER_SYSTEMS) - need 7 more (004 to 010)
power = [
    (
        "EX_EE_POW_004", "SKILL_POWER_ELECTRONICS",
        "In a single-phase half-bridge voltage source inverter (VSI) fed from a DC source V_dc with split capacitors, what is the peak-to-peak output voltage across the load?",
        {"A": "V_dc / 2", "B": "V_dc", "C": "2 * V_dc", "D": "V_dc / sqrt(2)"},
        "B",
        "In a half-bridge VSI with split DC rail (+/- V_dc/2), the pole switches connect the load between +V_dc/2 and -V_dc/2, giving a peak-to-peak swing of (+V_dc/2) - (-V_dc/2) = V_dc.",
        2.0, 3
    ),
    (
        "EX_EE_POW_005", "SKILL_POWER_ELECTRONICS",
        "Which power semiconductor device combines the simple gate-drive characteristics of MOSFETs with the high-current and low-saturation-voltage capability of bipolar transistors?",
        {"A": "TRIAC", "B": "IGBT", "C": "Schottky Diode", "D": "GTO"},
        "B",
        "The Insulated Gate Bipolar Transistor (IGBT) features a voltage-controlled MOS gate structure with a bipolar conduction output stage, offering high impedance drive and low on-state voltage drop.",
        1.5, 2
    ),
    (
        "EX_EE_POW_006", "SKILL_POWER_SYSTEMS",
        "In power system fault analysis, which type of unsymmetrical fault occurs most frequently in overhead transmission lines?",
        {"A": "Three-phase symmetrical fault (L-L-L)", "B": "Single line-to-ground fault (L-G)", "C": "Double line-to-ground fault (L-L-G)", "D": "Line-to-line fault (L-L)"},
        "B",
        "Single line-to-ground (L-G) faults account for approximately 70-80% of all transmission line faults, typically initiated by lightning strikes causing insulator flashover.",
        1.5, 2
    ),
    (
        "EX_EE_POW_007", "SKILL_POWER_SYSTEMS",
        "What is the surge impedance loading (SIL) of a lossless 400 kV transmission line having a surge impedance Z_c = 400 Ohm?",
        {"A": "100 MW", "B": "400 MW", "C": "1600 MW", "D": "1000 MW"},
        "B",
        "Surge Impedance Loading SIL = V_L^2 / Z_c = (400 kV)^2 / 400 Ohm = 160000 / 400 = 400 MW.",
        2.5, 3
    ),
    (
        "EX_EE_POW_008", "SKILL_POWER_SYSTEMS",
        "In Newton-Raphson load flow analysis, a generator bus (PV bus) has which two quantities specified as input variables?",
        {"A": "Active power P and reactive power Q", "B": "Active power P and voltage magnitude |V|", "C": "Voltage magnitude |V| and voltage angle delta", "D": "Reactive power Q and voltage angle delta"},
        "B",
        "At a PV (generator) bus, the net real power injection P and the bus voltage magnitude |V| are held constant by the governor and AVR; reactive power Q and phase angle delta are calculated.",
        2.0, 3
    ),
    (
        "EX_EE_POW_009", "SKILL_POWER_ELECTRONICS",
        "What is the duty ratio D required for a boost converter operating in continuous conduction mode (CCM) to step up a 12 V input to a 36 V output?",
        {"A": "0.33", "B": "0.67", "C": "0.50", "D": "0.75"},
        "B",
        "For a boost converter in CCM, V_out = V_in / (1 - D). Thus 36 = 12 / (1 - D) => 1 - D = 12 / 36 = 1/3 => D = 2/3 = 0.67 (66.7%).",
        2.0, 3
    ),
    (
        "EX_EE_POW_010", "SKILL_POWER_SYSTEMS",
        "The equal area criterion in power system stability analysis is applied to determine:",
        {"A": "Steady-state load flow convergence", "B": "Transient stability limit under sudden disturbances", "C": "Economic load dispatch between thermal plants", "D": "Harmonic distortion in transmission lines"},
        "B",
        "The equal area criterion is a graphical method based on the swing equation to assess transient stability of a single-machine infinite-bus (SMIB) system by equating accelerating and decelerating energy areas.",
        2.5, 3
    )
]

# 4. SIGNALS & DSP (SKILL_SIGNALS_SYSTEMS & SKILL_DSP) - need 9 more (002 to 010)
signals = [
    (
        "EX_EE_SIG_002", "SKILL_SIGNALS_SYSTEMS",
        "What is the Nyquist sampling rate for a bandlimited continuous signal x(t) having highest frequency component f_max = 4 kHz?",
        {"A": "4 kHz", "B": "8 kHz", "C": "16 kHz", "D": "2 kHz"},
        "B",
        "According to the Nyquist-Shannon sampling theorem, the minimum sampling rate to avoid aliasing is f_s = 2 * f_max = 2 * 4 kHz = 8 kHz.",
        1.5, 2
    ),
    (
        "EX_EE_SIG_003", "SKILL_SIGNALS_SYSTEMS",
        "A discrete-time linear time-invariant system has impulse response h[n] = (0.5)^n * u[n]. Is this system causal and BIBO stable?",
        {"A": "Non-causal and unstable", "B": "Causal and BIBO stable", "C": "Causal but unstable", "D": "Non-causal but stable"},
        "B",
        "Since h[n] = 0 for n < 0, the system is causal. The sum sum(|h[n]|) = sum_{n=0}^inf (0.5)^n = 1 / (1 - 0.5) = 2.0 < infinity, so the system is bounded-input bounded-output (BIBO) stable.",
        2.0, 3
    ),
    (
        "EX_EE_SIG_004", "SKILL_SIGNALS_SYSTEMS",
        "What is the Z-transform of the unit impulse sequence delta[n]?",
        {"A": "1 / (1 - z^(-1))", "B": "1", "C": "z / (z - 1)", "D": "0"},
        "B",
        "By definition, X(z) = sum_{n=-inf}^inf delta[n] * z^(-n) = delta[0] * z^0 = 1 for all complex z.",
        1.5, 2
    ),
    (
        "EX_EE_SIG_005", "SKILL_DSP",
        "In a radix-2 Decimation-in-Time (DIT) Fast Fourier Transform (FFT) algorithm, what is the computational complexity of computing an N-point DFT compared to the direct DFT complexity?",
        {"A": "O(N log2 N) compared to O(N^2)", "B": "O(N) compared to O(N log2 N)", "C": "O(N^2) compared to O(N^3)", "D": "O(log2 N) compared to O(N)"},
        "A",
        "Radix-2 FFT exploits symmetry and periodicity of twiddle factors, reducing required complex multiplications from O(N^2) in direct DFT to O(N * log2(N)).",
        2.0, 3
    ),
    (
        "EX_EE_SIG_006", "SKILL_DSP",
        "Which of the following window functions produces the highest peak side-lobe attenuation in FIR filter design?",
        {"A": "Rectangular window", "B": "Blackman window", "C": "Hanning window", "D": "Hamming window"},
        "B",
        "The Blackman window achieves approximately -58 dB peak side-lobe level (compared to -13 dB for Rectangular, -31 dB for Hanning, -41 dB for Hamming), offering superior stopband attenuation at the expense of wider mainlobe width.",
        2.5, 3
    ),
    (
        "EX_EE_SIG_007", "SKILL_DSP",
        "In digital filter design, what is the effect of the bilinear transformation s = (2/T) * (1 - z^(-1)) / (1 + z^(-1)) on frequency mapping?",
        {"A": "Linear mapping between analog and digital frequency", "B": "Nonlinear frequency warping from (-inf, +inf) into (-pi, +pi)", "C": "Causes aliasing in the digital domain", "D": "Shifts high frequencies into DC"},
        "B",
        "Bilinear transformation maps the entire imaginary j*Omega axis of the s-plane uniquely into one revolution of the unit circle in the z-plane, eliminating aliasing through a nonlinear frequency warping relationship: omega = 2 * arctan(Omega * T / 2).",
        2.5, 3
    ),
    (
        "EX_EE_SIG_008", "SKILL_SIGNALS_SYSTEMS",
        "What is the Fourier transform of the signum function sgn(t)?",
        {"A": "2 / (j * omega)", "B": "1 / (j * omega)", "C": "pi * delta(omega)", "D": "j * omega"},
        "A",
        "Expressing sgn(t) = lim_{a->0} (e^(-at) u(t) - e^(at) u(-t)), taking Fourier transforms yields 1/(a + j*omega) - 1/(a - j*omega) -> 2 / (j * omega).",
        2.5, 3
    ),
    (
        "EX_EE_SIG_009", "SKILL_DSP",
        "What ensures that an FIR filter has strictly linear phase?",
        {"A": "The filter order must be odd", "B": "The impulse response h[n] must possess even or odd symmetry around its midpoint", "C": "All poles must lie inside the unit circle", "D": "The filter must be recursive"},
        "B",
        "Linear phase is guaranteed if and only if the impulse response satisfies symmetry h[n] = h[N - 1 - n] (symmetric) or h[n] = -h[N - 1 - n] (antisymmetric), preserving waveform shape without phase distortion.",
        2.0, 3
    ),
    (
        "EX_EE_SIG_010", "SKILL_SIGNALS_SYSTEMS",
        "If a continuous-time signal x(t) has Laplace transform X(s) with Region of Convergence (ROC) Re(s) > 2, what can be deduced about the signal x(t)?",
        {"A": "It is a left-sided anti-causal signal", "B": "It is a right-sided causal signal", "C": "It is a finite-duration two-sided signal", "D": "It is periodic"},
        "B",
        "An ROC of the form Re(s) > sigma_0 (right-half plane) corresponds to a right-sided signal; if rational, it corresponds to a causal signal.",
        2.0, 3
    )
]

# 5. DATA STRUCTURES & ALGORITHMS (SKILL_DATA_STRUCTURES_ALGO) - 10 exercises
dsa = [
    (
        "EX_CS_DSA_001", "SKILL_DATA_STRUCTURES_ALGO",
        "What is the worst-case time complexity of searching an element in a balanced Binary Search Tree (AVL or Red-Black Tree) containing N elements?",
        {"A": "O(1)", "B": "O(log N)", "C": "O(N)", "D": "O(N log N)"},
        "B",
        "In balanced binary search trees, the height is strictly bounded by O(log N). Traversing from root to leaf takes at most O(log N) comparisons.",
        1.5, 2
    ),
    (
        "EX_CS_DSA_002", "SKILL_DATA_STRUCTURES_ALGO",
        "Which sorting algorithm has a worst-case time complexity of O(N log N) and can be easily implemented as a stable sort on linked lists?",
        {"A": "Quick Sort", "B": "Merge Sort", "C": "Heap Sort", "D": "Selection Sort"},
        "B",
        "Merge Sort consistently achieves O(N log N) in best, average, and worst cases, maintains stability, and can sort linked lists in O(1) auxiliary space without extra array allocation.",
        2.0, 3
    ),
    (
        "EX_CS_DSA_003", "SKILL_DATA_STRUCTURES_ALGO",
        "In Dijkstra algorithm for finding single-source shortest paths on a graph with V vertices and E edges using a min-priority heap, what is the overall running time?",
        {"A": "O(V^2)", "B": "O((V + E) log V)", "C": "O(E * V)", "D": "O(V log E)"},
        "B",
        "Using a binary min-heap, extracting min takes O(log V) across V vertices, and edge relaxation updates take O(E log V), yielding total complexity O((V + E) log V).",
        2.5, 4
    ),
    (
        "EX_CS_DSA_004", "SKILL_DATA_STRUCTURES_ALGO",
        "What data structure is used to implement Breadth-First Search (BFS) graph traversal?",
        {"A": "Stack", "B": "Queue", "C": "Priority Queue", "D": "Binary Search Tree"},
        "B",
        "BFS explores vertices in order of their distance from the source vertex in FIFO order, which is implemented using a First-In-First-Out Queue.",
        1.5, 2
    ),
    (
        "EX_CS_DSA_005", "SKILL_DATA_STRUCTURES_ALGO",
        "In hash tables with open addressing and linear probing, what phenomenon causes clusters of occupied slots to grow, degrading lookup performance?",
        {"A": "Secondary clustering", "B": "Primary clustering", "C": "Hash collision decay", "D": "Rehashing stagnation"},
        "B",
        "Primary clustering occurs in linear probing when consecutive occupied slots form contiguous blocks; any key hashing into the block extends the cluster.",
        2.0, 3
    ),
    (
        "EX_CS_DSA_006", "SKILL_DATA_STRUCTURES_ALGO",
        "What is the space complexity of a standard recursive Depth-First Search (DFS) on a general graph with V vertices?",
        {"A": "O(V) for the recursion call stack and visited array", "B": "O(V * E)", "C": "O(1)", "D": "O(E)"},
        "A",
        "In the worst case (e.g., linear chain graph), the recursion stack reaches depth V, requiring O(V) stack space along with an O(V) boolean visited array.",
        2.0, 3
    ),
    (
        "EX_CS_DSA_007", "SKILL_DATA_STRUCTURES_ALGO",
        "What dynamic programming approach solves the 0/1 Knapsack problem with N items and capacity W in O(N * W) time?",
        {"A": "Greedy choice by value/weight ratio", "B": "2D table storing optimal value for items 1..i and capacity w", "C": "Divide and conquer with independent subproblems", "D": "Branch and bound traversal"},
        "B",
        "The recurrence DP[i][w] = max(DP[i-1][w], val[i] + DP[i-1][w - wt[i]]) evaluates subproblems systematically in O(N * W) pseudo-polynomial time.",
        2.5, 4
    ),
    (
        "EX_CS_DSA_008", "SKILL_DATA_STRUCTURES_ALGO",
        "In a max-heap of size N, what is the time complexity of inserting a new element?",
        {"A": "O(1)", "B": "O(log N)", "C": "O(N)", "D": "O(N log N)"},
        "B",
        "The new element is placed at the end of the heap array and sifted up (bubble up) along the tree height, which requires at most O(log N) comparisons and swaps.",
        1.5, 2
    ),
    (
        "EX_CS_DSA_009", "SKILL_DATA_STRUCTURES_ALGO",
        "Which algorithmic design paradigm does Kruskal algorithm for finding the Minimum Spanning Tree (MST) belong to?",
        {"A": "Dynamic Programming", "B": "Greedy Algorithm", "C": "Backtracking", "D": "Divide and Conquer"},
        "B",
        "Kruskal algorithm greedily sorts all edges by ascending weight and adds the lightest edge that does not form a cycle (using Disjoint-Set / Union-Find).",
        2.0, 3
    ),
    (
        "EX_CS_DSA_010", "SKILL_DATA_STRUCTURES_ALGO",
        "What is the amortized time complexity of inserting an element into a dynamic array (like Python list or C++ std::vector) that doubles capacity when full?",
        {"A": "O(N)", "B": "O(1)", "C": "O(log N)", "D": "O(N^2)"},
        "B",
        "Although resizing takes O(N) copy operations once every N elements, the total cost for N insertions is O(2N) = O(N), yielding an amortized cost of O(1) per insertion.",
        2.0, 3
    )
]

# 6. METALLURGICAL THERMODYNAMICS & PHYSICAL METALLURGY - 10 exercises
metallurgy = [
    (
        "EX_MM_MET_001", "SKILL_THERMODYNAMICS_MAT",
        "According to the Gibbs Phase Rule P + F = C + 2, how many degrees of freedom F exist for a pure single-component metal (C=1) at its equilibrium melting point where solid and liquid coexist (P=2)?",
        {"A": "0", "B": "1", "C": "2", "D": "3"},
        "B",
        "Applying Gibbs Phase Rule: F = C - P + 2 = 1 - 2 + 2 = 1 (univariant equilibrium). If pressure is fixed at 1 atm, F = 0 (an invariant melting temperature).",
        2.0, 3
    ),
    (
        "EX_MM_MET_002", "SKILL_THERMODYNAMICS_MAT",
        "In an Ellingham diagram, why do lines representing the standard free energy of oxide formation (Delta G_0 vs T) generally have a positive slope?",
        {"A": "Oxidation reactions are endothermic", "B": "Oxygen gas is consumed, causing a decrease in entropy (Delta S < 0)", "C": "The equilibrium constant increases with temperature", "D": "Oxides decompose at high temperature"},
        "B",
        "In reactions 2M + O2(g) -> 2MO(s), one mole of gas is converted to solid, leading to a negative entropy change Delta S_0 < 0. Since d(Delta G)/dT = -Delta S, the slope -Delta S is positive.",
        2.5, 3
    ),
    (
        "EX_MM_MET_003", "SKILL_PHYSICAL_METALLURGY",
        "What is the crystal structure and number of atoms per unit cell in face-centered cubic (FCC) metals such as copper and austenite (gamma-iron)?",
        {"A": "BCC with 2 atoms/cell", "B": "FCC with 4 atoms/cell", "C": "HCP with 6 atoms/cell", "D": "Simple cubic with 1 atom/cell"},
        "B",
        "FCC has 8 corner atoms (8 * 1/8 = 1) and 6 face-centered atoms (6 * 1/2 = 3), totaling 4 atoms per unit cell with close-packed {111} planes.",
        1.5, 2
    ),
    (
        "EX_MM_MET_004", "SKILL_PHYSICAL_METALLURGY",
        "Which diffusionless shear transformation occurs in carbon steels upon rapid quenching from the austenite phase?",
        {"A": "Pearlite formation", "B": "Martensitic transformation", "C": "Bainitic reaction", "D": "Spheroidization"},
        "B",
        "Rapid cooling (quenching) suppresses carbon diffusion, forcing the FCC austenite lattice to undergo a military/shear displacement into a supersaturated, hard Body-Centered Tetragonal (BCT) martensite structure.",
        2.0, 3
    ),
    (
        "EX_MM_MET_005", "SKILL_PHYSICAL_METALLURGY",
        "In precipitation hardening (age hardening) of Al-4wt%Cu alloys, what is the correct sequence of microstructural precipitation upon aging?",
        {"A": "Supersaturated solid solution -> GP zones -> theta double-prime -> theta prime -> equilibrium theta (CuAl2)", "B": "Austenite -> Martensite -> Tempered Martensite", "C": "Ferrite -> Cementite -> Pearlite", "D": "Liquid -> Ingot -> Dendrite"},
        "A",
        "Age hardening progresses through coherent Guinier-Preston (GP) zones, semi-coherent metastable precipitates (theta double-prime, theta prime), and finally the incoherent equilibrium theta (CuAl2) phase.",
        3.0, 4
    ),
    (
        "EX_MM_MET_006", "SKILL_THERMODYNAMICS_MAT",
        "What condition defines Raoultian ideal solution behavior for a binary metallic alloy component A?",
        {"A": "Activity a_A = 1 at all concentrations", "B": "Activity a_A is equal to its mole fraction X_A (activity coefficient gamma_A = 1)", "C": "Enthalpy of mixing is strongly exothermic", "D": "Volume of mixing increases by 50%"},
        "B",
        "In an ideal Raoultian solution, interatomic bond energies between A-A, B-B, and A-B are identical, meaning Delta H_mix = 0, Delta V_mix = 0, and activity a_A = X_A (activity coefficient gamma_A = 1.0).",
        2.0, 3
    ),
    (
        "EX_MM_MET_007", "SKILL_PHYSICAL_METALLURGY",
        "According to the Hall-Petch equation, how does the yield strength sigma_y of a polycrystalline metal vary with average grain diameter d?",
        {"A": "sigma_y = sigma_0 + k_y * d", "B": "sigma_y = sigma_0 + k_y * d^(-1/2)", "C": "sigma_y = sigma_0 - k_y * d^2", "D": "sigma_y is independent of grain size"},
        "B",
        "The Hall-Petch relationship states sigma_y = sigma_0 + k_y / sqrt(d), meaning finer grains create more grain boundaries that obstruct dislocation motion, increasing yield strength.",
        2.0, 3
    ),
    (
        "EX_MM_MET_008", "SKILL_THERMODYNAMICS_MAT",
        "In a unary system, the Clausius-Clapeyron equation dP/dT = Delta H / (T * Delta V) describes:",
        {"A": "The rate of chemical reaction kinetics", "B": "The slope of the phase equilibrium boundary on a P-T diagram", "C": "The electrical conductivity of liquid slag", "D": "The diffusion coefficient as a function of temperature"},
        "B",
        "The Clausius-Clapeyron equation relates the change in equilibrium pressure with temperature along a coexistence curve to the latent heat of transformation Delta H and volume change Delta V.",
        2.5, 3
    ),
    (
        "EX_MM_MET_009", "SKILL_PHYSICAL_METALLURGY",
        "What type of crystal defect is an edge dislocation?",
        {"A": "Point defect", "B": "Linear (one-dimensional) defect", "C": "Planar (two-dimensional) defect", "D": "Volume defect"},
        "B",
        "An edge dislocation represents an extra half-plane of atoms inserted into the crystal lattice, characterized by its dislocation line and Burgers vector perpendicular to it, classifying it as a 1D linear defect.",
        1.5, 2
    ),
    (
        "EX_MM_MET_010", "SKILL_PHYSICAL_METALLURGY",
        "In the iron-carbon equilibrium phase diagram, the eutectoid reaction occurring at 727 deg C and 0.76 wt% C is:",
        {"A": "Liquid -> Austenite + Cementite (Ledeburite)", "B": "Austenite (gamma) -> Ferrite (alpha) + Cementite (Fe3C) [Pearlite]", "C": "Delta-ferrite + Liquid -> Austenite", "D": "Liquid -> Ferrite + Austenite"},
        "B",
        "The eutectoid reaction involves solid austenite (gamma) decomposing cooperatively at 727 deg C into lamellar alternating plates of ferrite (alpha) and iron carbide / cementite (Fe3C), known as pearlite.",
        2.0, 3
    )
]

all_groups = [circuits, machines, power, signals, dsa, metallurgy]
for grp in all_groups:
    for item in grp:
        new_exercises.append(make_ex(*item))

# Combine existing and new
total_records = existing_records + new_exercises
print(f"Total exercises: {len(total_records)}")

# Write to data/seed/kb/exercise.csv
out_path = 'data/seed/kb/exercise.csv'
fieldnames = ['exercise_id', 'skill_id', 'module_id', 'kind', 'difficulty', 'prompt', 'options', 'answer_key', 'rubric', 'est_minutes', 'status', 'source_id', 'licence', 'source_url']

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in total_records:
        writer.writerow(r)

print(f"Successfully generated and wrote {len(total_records)} exercises to {out_path}.")
