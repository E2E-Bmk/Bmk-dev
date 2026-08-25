def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'depends_on(*nodeids): documents atomic tests an integration test depends on')
