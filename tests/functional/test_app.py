def test_zf_app_home(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN the home page is requested
    THEN returns an HTML page with 200
    """
    res = client_new.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("Content-Type")
    assert "html" in res.text


def test_zf_app_zone(client_single_zone):
    """
    GIVEN a web client for a newly initialized server
    WHEN a zome's page is requested
    THEN returns an HTML page with 200
    """
    res = client_single_zone.get("/zone/example.com.")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("Content-Type")
    assert "html" in res.text


def test_zf_app_login(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN the login page is requested
    THEN returns an HTML page with 200
    """
    res = client_new.get("/login")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("Content-Type")
    assert "html" in res.text


def test_zf_app_signup(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN the signup page is requested
    THEN returns an HTML page with 200
    """
    res = client_new.get("/signup")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("Content-Type")
    assert "html" in res.text
