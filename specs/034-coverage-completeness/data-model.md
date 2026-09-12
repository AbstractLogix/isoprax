# Data Model

Coverage gate state is the comparison:

```text
expected source modules - reported coverage modules = missing failures
```

`__init__.py` remains excluded. Every other production Python module must have
coverage JSON with a `summary.percent_covered` value.
