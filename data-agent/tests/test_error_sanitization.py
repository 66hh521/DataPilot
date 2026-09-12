from app.core.errors import ErrorCode, sanitize_exception, user_message


def test_html_error_is_not_exposed():
    error = RuntimeError("<!DOCTYPE html><html><h1>Request Blocked</h1></html>")
    assert sanitize_exception(error) == user_message(ErrorCode.EXTERNAL_SERVICE_ERROR)


def test_plain_error_is_bounded():
    message = sanitize_exception(RuntimeError("x" * 1000))
    assert len(message) == 300
