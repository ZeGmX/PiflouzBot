class Custom_Assert_Exception(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)