from streamlit.testing.v1 import AppTest


def test_app_starts_dark_with_generation_disabled() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert app.session_state.theme == "dark"
    assert any(">pdf-it<" in element.value for element in app.markdown)
    assert len(app.text_area) == 3
    assert len(app.file_uploader) == 1
    assert next(button for button in app.button if button.label == "Create PDF").disabled


def test_source_and_key_enable_generation() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)
    app.text_area[0].input("A short source document.")
    app.text_input[0].input("unit-test-key")
    app.run(timeout=20)

    assert not app.exception
    assert not next(button for button in app.button if button.label == "Create PDF").disabled


def test_theme_toggle_updates_session() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)
    assert app.segmented_control[0].value == "Dark"
    app.segmented_control[0].set_value("Light")
    app.run(timeout=20)
    assert app.session_state.theme == "light"
    app.segmented_control[0].set_value("Dark")
    app.run(timeout=20)
    assert app.session_state.theme == "dark"
