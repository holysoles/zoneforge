import pytest
from flask import Flask

@pytest.fixture(scope='module')
def app():
    app = Flask(__name__)
    return app