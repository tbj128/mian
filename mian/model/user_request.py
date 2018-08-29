
class UserRequest(object):

    def __init__(self, user_id, pid, taxonomy_filter_count, taxonomy_filter_prevalence, taxonomy_filter,
                 taxonomy_filter_role, taxonomy_filter_vals, sample_filter, sample_filter_role, sample_filter_vals,
                 level, catvar):
        self.user_id = user_id
        self.pid = pid
        self.taxonomy_filter_count = float(taxonomy_filter_count) if taxonomy_filter_count else 0
        self.taxonomy_filter_prevalence = float(taxonomy_filter_prevalence) if taxonomy_filter_prevalence else 0
        self.taxonomy_filter = taxonomy_filter
        self.taxonomy_filter_role = taxonomy_filter_role
        self.taxonomy_filter_vals = taxonomy_filter_vals
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
