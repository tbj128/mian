from abc import ABCMeta, abstractmethod


class AnalysisBase(metaclass=ABCMeta):

    @abstractmethod
    def run(self, user_request):
        pass
