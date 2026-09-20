# JEPA Strategy Contract

The public implementation is `isoprax.jepa`.

## Training

```python
model = JEPAWorldModel(JEPABackendConfig(...))
report = model.fit([JEPATrainingPair(change, pre_state, post_state)])
```

`fit` is deterministic, self-supervised, offline, and rejects empty, inconsistent,
or non-finite input. Calling readout methods before fitting raises `ValueError`.

## Readouts

```python
risk = JEPARiskStrategy(model, calibrator=Calibrator())
anomaly = JEPAAnomalyStrategy(model, calibrator=Calibrator())
risk_signal = risk.score(change, {})
anomaly_signal = anomaly.evaluate(
    run,
    {
        "change": change,
        "pre_state": pre_state,
        "post_state": post_state,
    },
)
```

The risk adapter uses only the change representation. The anomaly adapter requires
both state windows and scores the predictor's latent error against the observed post
state. Both signals use the existing signal fields and report calibration status
honestly.

## Conformance

`model.assess()` returns Structural evidence by default. `model.assess(evidence)`
returns Semantic only when the evidence identifies the exact fitted backend and
state representation, carries the backend-derived shared-representation proof,
marks the representation non-decomposable, and contains finite non-constant
evidence for both readouts. It does not alter Outcome Definition commensurability
or authorize pooled scores.
