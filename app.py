from test.test_app import test_page, Authenticate


if __name__ == '__main__':
    Authenticate.create_admin_if_not_exists()
    test_page()
