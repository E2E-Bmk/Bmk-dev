# Spec2Repo oracle - pytest marker registration for dnspython-fullrepro-001


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public primitive dependencies for integration-gap analysis")
