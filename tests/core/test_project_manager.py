from mian.core.project_manager import ProjectManager
from mian.core.data_io import DataIO
import unittest
import os
import shutil
import numpy as np


class TestProjectManager(unittest.TestCase):
    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "mian"))
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    UNIT_TESTS_DIRECTORY = os.path.join(DATA_DIRECTORY, "unit_tests")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def test__create_project_from_tsv(self):
        project_manager = ProjectManager("unit_tests")

        unit_tests_dir = os.path.join(TestProjectManager.UNIT_TESTS_DIRECTORY, "small_biom")
        test_staging_dir = os.path.join(TestProjectManager.STAGING_DIRECTORY, "unit_tests")
        if not os.path.exists(test_staging_dir):
            os.makedirs(test_staging_dir)

        shutil.copyfile(os.path.join(unit_tests_dir, "table.raw.tsv"), os.path.join(test_staging_dir, "table.raw.tsv"))
        shutil.copyfile(os.path.join(unit_tests_dir, "otu_taxonomy.txt"), os.path.join(test_staging_dir, "otu_taxonomy.txt"))
        shutil.copyfile(os.path.join(unit_tests_dir, "sample_metadata.txt"),
                        os.path.join(test_staging_dir, "sample_metadata.txt"))

        pid = project_manager.create_project_from_tsv("tmp_project", "table.raw.tsv",
                                                      "otu_taxonomy.txt", "sample_metadata.txt")

        test_project_dir = os.path.join(TestProjectManager.UNIT_TESTS_DIRECTORY, pid)
        self.assertTrue(os.path.exists(test_project_dir))

        subsampled_table = DataIO.tsv_to_np_table("unit_tests", pid, "table.subsampled.tsv")
        self.assertEqual(6, len(subsampled_table))

        r = 0
        while r < len(subsampled_table):
            self.assertEqual(30, np.sum(subsampled_table[r]))
            r += 1

        subsampled_table_labels = DataIO.tsv_to_table("unit_tests", pid, "table.subsampled.labels.tsv")
        self.assertEqual(2, len(subsampled_table_labels))
        self.assertEqual(5, len(subsampled_table_labels[0]))
        self.assertEqual(6, len(subsampled_table_labels[1]))

        shutil.rmtree(test_project_dir)


    def test__create_project_from_biom(self):
        project_manager = ProjectManager("unit_tests")

        unit_tests_dir = os.path.join(TestProjectManager.UNIT_TESTS_DIRECTORY, "small_biom")
        test_staging_dir = os.path.join(TestProjectManager.STAGING_DIRECTORY, "unit_tests")
        if not os.path.exists(test_staging_dir):
            os.makedirs(test_staging_dir)

        shutil.copyfile(os.path.join(unit_tests_dir, "table.biom"), os.path.join(test_staging_dir, "table.biom"))

        pid = project_manager.create_project_from_biom("tmp_project", "table.biom")

        test_project_dir = os.path.join(TestProjectManager.UNIT_TESTS_DIRECTORY, pid)
        self.assertTrue(os.path.exists(test_project_dir))

        subsampled_table = DataIO.tsv_to_np_table("unit_tests", pid, "table.subsampled.tsv")
        self.assertEqual(6, len(subsampled_table))

        r = 0
        while r < len(subsampled_table):
            self.assertEqual(30, np.sum(subsampled_table[r]))
            r += 1

        subsampled_table_labels = DataIO.tsv_to_table("unit_tests", pid, "table.subsampled.labels.tsv")
        self.assertEqual(2, len(subsampled_table_labels))
        self.assertEqual(5, len(subsampled_table_labels[0]))
        self.assertEqual(6, len(subsampled_table_labels[1]))

        shutil.rmtree(test_project_dir)

    def test__decompose_silva_taxonomy(self):
        project_manager = ProjectManager("unit_tests")
        expected_output = ["Bacteria", "Bacteroidetes", "Flavobacteria", "Flavobacteriales", "Flavobacteriaceae", "Chryseobacterium", "meningosepticum"]
        actual_output = project_manager.process_taxonomy_line("Silva",
                                                              "Bacteria(100);\"Bacteroidetes\"(100);Flavobacteria(100);\"Flavobacteriales\"(100);Flavobacteriaceae(100);Chryseobacterium(100);meningosepticum(100)")
        self.assertEqual(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Silva",
                                                              "Bacteria;Bacteroidetes;Flavobacteria;Flavobacteriales;Flavobacteriaceae;Chryseobacterium;meningosepticum")
        self.assertEqual(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Silva",
                                                              ["Bacteria(100)", "Bacteroidetes", "Flavobacteria[98]",
                                                               "Flavobacteriales", "Flavobacteriaceae",
                                                               "[100]Chryseobacterium", "meningosepticum"])
        self.assertEqual(expected_output, actual_output)


    def test__decompose_gg_taxonomy(self):
        project_manager = ProjectManager("unit_tests")
        expected_output = ["Bacteria", "Bacteroidetes", "Flavobacteria", "Flavobacteria", "Flavobacteriaceae", "Chryseobacterium", "meningosepticum"]
        actual_output = project_manager.process_taxonomy_line("Greengenes",
                                                              "k__Bacteria(100);\"p__Bacteroidetes\"(100);c__Flavobacteria(100);\"o__Flavobacteria\"(100);f__Flavobacteriaceae(100);g__Chryseobacterium(100);s__meningosepticum(100)")
        self.assertEqual(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Greengenes",
                                                              "k__Bacteria;p__Bacteroidetes;c__Flavobacteria;o__Flavobacteria;f__Flavobacteriaceae;g__Chryseobacterium;s__meningosepticum")
        self.assertEqual(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Greengenes",
                                                              ["k__Bacteria(100)", "p__Bacteroidetes", "c__Flavobacteria[98]",
                                                               "o__Flavobacteria", "f__Flavobacteriaceae",
                                                               "[100]g__Chryseobacterium", "s__meningosepticum"])
        self.assertEqual(expected_output, actual_output)


if __name__ == '__main__':
    unittest.main()