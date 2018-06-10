# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#

import os
import csv
from scipy import stats
import math
import random
import string
import numpy as np
import shutil
import json
from subprocess import Popen, PIPE
from datetime import datetime


class Project(object):
    @staticmethod
    def add_file_name_attr(csv_name, postfix, attr):
        """
        Adds an attribute right before the last dot of the postfix
        :param csv_name:
        :param postfix:
        :param attr:
        :return:
        """
        csv_name = csv_name.lower().replace("." + postfix, "")
        csv_name = csv_name + "." + attr + "." + postfix
        return csv_name

    @staticmethod
    def change_map_filename(user, pid, fileType, newFilename):
        """
        Updates a file type with a new file type.

        Args:
            user (str): The user ID of the associated account
            pid (str): The project ID under the user account
            fileType (str): The file type
            newFilename (str): The new file name of the file type

        """

        dir = os.path.dirname(__file__)
        dir = os.path.join(dir, "data")
        dir = os.path.join(dir, user)
        dir = os.path.join(dir, pid)
        mapPath = os.path.join(dir, 'map.txt')

        item = {}
        with open(mapPath) as outfile:
            item = json.load(outfile)
        item[fileType] = newFilename

        with open(mapPath, 'w') as outfile:
            json.dump(item, outfile)

    @staticmethod
    def change_map_subsample_type(user, pid, subsample_type):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user)
        project_dir = os.path.join(project_dir, pid)
        mapPath = os.path.join(project_dir, 'map.txt')

        item = {}
        with open(mapPath) as outfile:
            item = json.load(outfile)
        item["subsample_type"] = subsample_type

        with open(mapPath, 'w') as outfile:
            json.dump(item, outfile)

    @staticmethod
    def change_map_subsample_val(user, pid, subsample_to):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user)
        project_dir = os.path.join(project_dir, pid)
        mapPath = os.path.join(project_dir, 'map.txt')

        with open(mapPath) as outfile:
            item = json.load(outfile)
        item["subsampleVal"] = subsample_to

        with open(mapPath, 'w') as outfile:
            json.dump(item, outfile)
