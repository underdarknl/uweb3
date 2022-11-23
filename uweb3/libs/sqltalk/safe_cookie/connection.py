class Connection:
    def __init__(self, request, cookies, cookie_salt, autocommit=True, **kwargs):
        self.autocommit_mode = autocommit
        self.request_object = request
        self.cookies = cookies
        self.cookie_salt = cookie_salt
        self.uncommitted_cookies = []

        if kwargs.pop("debug", True):
            self.debug = True
        else:
            self.debug = False

    def insert(self, key, value, **kwds):
        if self.autocommit_mode:
            self.request_object.AddCookie(key, value, **kwds)
        else:
            self.uncommitted_cookies.append(
                {"key": key, "value": value, "action": "insert", **kwds}
            )

    def update(self, key, value, **kwds):
        self.insert(key, value, **kwds)

    def delete(self, name):
        if self.autocommit_mode:
            self.request_object.DeleteCookie(name)
        else:
            self.uncommitted_cookies.append({"name": name, "action": "delete"})

    def rollback(self):
        del self.uncommitted_cookies[:]

    def autocommit(self, value):
        self.autocommit_mode = value

    def commit(self):
        for cookie in self.uncommitted_cookies:
            if cookie["action"] == "insert":
                del cookie["action"]
                self.request_object.AddCookie(**cookie)
            elif cookie["action"] == "delete":
                del cookie["action"]
                self.request_object.DeleteCookie(**cookie)
            else:
                # When this error is raised the list is not propperly cleared.
                raise NotImplementedError(
                    "This action type is currently not supported."
                )
        del self.uncommitted_cookies[:]
