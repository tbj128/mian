
class UserRequest(object):

    def __init__(self, user_id, pid, sample_filter, sample_filter_role, sample_filter_vals,
                 level, catvar):
        self.user_id = user_id
        self.pid = pid
        self.sample_filter = sample_filter
        self.sample_filter_role = sample_filter_role
        self.sample_filter_vals = sample_filter_vals
        self.level = level
        self.catvar = catvar
        self.custom_attrs = {}

    def set_custom_attr(self, key, val):
        self.custom_attrs[key] = val

    def remove_custom_attr(self, key):
        del self.custom_attrs[key]

    def get_custom_attr(self, key):
        return self.custom_attrs[key]
