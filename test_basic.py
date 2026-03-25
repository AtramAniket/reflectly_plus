from app import create_app

def test_app_exists():
    app = create_app()
    assert app is not None