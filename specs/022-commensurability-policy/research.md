# Research: Unified Commensurability Policy

`check_commensurable` already models direct, attested, bridgeable, and
irreducible levels. `require_commensurable` discarded its optional policy
inputs, and `cross_family_report` tested `commensurable` instead of
`pooling_allowed`. That made the retained-observation bridge unreachable in
one API and inconsistent in another.
