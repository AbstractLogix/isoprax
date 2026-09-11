# Research: Evaluation Diagnostic Input Integrity

The primitives delegated validation to NumPy. Empty Brier inputs returned
`nan`, mismatched ECE inputs surfaced internal indexing errors, and a train
fraction greater than one silently produced no test rows. The conformance
wrapper already had stricter checks; this slice makes the underlying public
diagnostics consistent.
