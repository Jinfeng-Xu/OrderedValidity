# Contributing

Contributions extend the finite population contract through tested schemas and adapters.

1. Add tests for every schema or decision change.
2. Keep failed and missing positions in the denominator.
3. Declare the molecular identity relation and dependence unit explicitly.
4. Keep archive specific molecular parsing in an adapter and keep the core evaluator lightweight.
5. Treat protocol changes as semantic changes and document them explicitly.
6. Include a minimal fixture and regression test with every new adapter.

Run `pytest` and validate the example protocol before opening a change:

```bash
ordered-validity validate-protocol configs/example-protocol.json
```

