"""MAKU risk methodology version.

Bump this whenever a formula, threshold, band edge, control rule or residual-
risk rule changes, and record the change in docs/METHODOLOGY.md. Every
assessment result and report carries the version that produced it, so a
past report can always be traced to the exact rules behind it.

  MAJOR - a change that can move an existing result to a different band or
          residual score (e.g. 2.0.0: residual risk credits only controls
          that address the hazard)
  MINOR - new module, new input or new control that does not change
          existing results
  PATCH - wording, documentation, refactoring with identical results
"""
METHODOLOGY_VERSION = "2.0.0"
METHODOLOGY_DATE = "2026-10-14"
