def raises(kind, operation):
    try: operation()
    except kind: return
    raise AssertionError(f"expected {kind.__name__}")
