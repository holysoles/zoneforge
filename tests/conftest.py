import pytest
from app import create_app
import os

@pytest.fixture()
def app(tmp_path):
    zonefile_folder = str(tmp_path)
    os.environ['ZONE_FILE_FOLDER'] = zonefile_folder

    app = create_app()
    app.config.update({
        "TESTING": True,
        "ZONE_FILE_FOLDER": zonefile_folder
    })

    app.app_context().push()

    yield app