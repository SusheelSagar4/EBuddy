# Course Skill Mapping Corrections

This document records the 10 data corrections applied to `data/seed/kb/course_skill.csv` to resolve skill classification anomalies in seed data.

## Before and After Comparison Table

| course_id | course_title | before_skill_id | before_skill_name | after_skill_id | after_skill_name | reason |
|---|---|---|---|---|---|---|
| `EC6L005` | Statistical Signal Processing | `SKILL_EMBEDDED_SYSTEMS` | Embedded Systems & Real-Time Computing | `SKILL_DSP` | Digital Signal Processing & Filtering | Statistical signal processing is mathematical estimation and filtering theory, not embedded systems firmware/hardware. |
| `EC2L006` | Digital Electronics and Microprocessor | `SKILL_EM_FIELDS` | Electromagnetics & Transmission Lines | `SKILL_DIGITAL_LOGIC` | Digital Logic & Microprocessors | Logic gates, flip-flops, and microprocessors belong to digital logic, not electromagnetics. |
| `EC3L003` | Digital Signal Processing | `SKILL_DIGITAL_LOGIC` | Digital Logic & Microprocessors | `SKILL_DSP` | Digital Signal Processing & Filtering | DSP theory is discrete-time transform analysis and filter design, not digital logic. |
| `EC3P002` | Digital Signal Processing Laboratory | `SKILL_DIGITAL_LOGIC` | Digital Logic & Microprocessors | `SKILL_DSP` | Digital Signal Processing & Filtering | Laboratory for discrete-time signal processing and filter implementation. |
| `EE3L004` | Power Electronics | `SKILL_POWER_SYSTEMS` | Power System Analysis & Grid Operations | `SKILL_POWER_ELECTRONICS` | Power Electronic Converters & Drives | Solid-state converters, inverters, and choppers belong to power electronics, not bulk grid operations. |
| `EE3P004` | Power Electronics Laboratory | `SKILL_POWER_SYSTEMS` | Power System Analysis & Grid Operations | `SKILL_POWER_ELECTRONICS` | Power Electronic Converters & Drives | Lab experimenting with power electronic semiconductor switches and converters. |
| `EE3P006` | Power Systems Laboratory | `SKILL_POWER_ELECTRONICS` | Power Electronic Converters & Drives | `SKILL_POWER_SYSTEMS` | Power System Analysis & Grid Operations | Power Systems Lab was inverted in seed data; remapped to power systems. |
| `EE3L007` | Electrical Power Transmission and Distribution | `SKILL_ELECTRIC_MACHINES` | Electrical Machines & Electromechanics | `SKILL_POWER_SYSTEMS` | Power System Analysis & Grid Operations | Transmission lines, substations, and grid networks belong to power systems, not rotating electrical machines. |
| `EE3L008` | Soft Computing and Applications | `SKILL_POWER_ELECTRONICS` | Power Electronic Converters & Drives | `SKILL_AI_ML` | Machine Learning & Pattern Recognition | Neural networks, fuzzy logic, and genetic optimization algorithms belong to AI/ML, not power electronics converters. |
| `EE3L005` | Control System Technology | `SKILL_INSTRUMENTATION` | Instrumentation, Transducers & Sensors | `SKILL_CONTROL_SYSTEMS` | Classical & Modern Feedback Control | State-space feedback control and system compensation belong to control systems, not sensors/instrumentation. |
| `EE4L004` | Advanced Electric Machines | `SKILL_POWER_SYSTEMS` | Power System Analysis & Grid Operations | `SKILL_ELECTRIC_MACHINES` | Electrical Machines & Electromechanics | Advanced rotating machines and electromechanics belongs to electrical machines. |
| `ML4L003_CORE` | Polymers and nanocomposites | `SKILL_CORROSION_SURFACE` | Corrosion & Surface Engineering | *(REMOVED)* | *(REMOVED)* | Removed anomalous secondary mapping to corrosion; primary mapping to `SKILL_COMPOSITES_NANO` is retained. |
