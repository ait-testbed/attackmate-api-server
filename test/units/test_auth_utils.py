from attackmate_api_server.auth_utils import password_hasher, verify_password


def test_verify_password() -> None:
    hashed = password_hasher.hash('secret')
    assert verify_password('secret', hashed)
    assert not verify_password('wrong', hashed)
    assert not verify_password('secret', 'not-a-hash')
