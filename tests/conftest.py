import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests - isolated function/class tests")
    config.addinivalue_line("markers", "integration: Integration tests - tests with external dependencies")
    config.addinivalue_line("markers", "e2e: End-to-end tests - full system tests")
