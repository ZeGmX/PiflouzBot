class CustomAssertError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CustomTaskError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
