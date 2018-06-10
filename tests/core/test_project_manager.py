from core.project_manager import ProjectManager
import unittest


class TestProjectManager(unittest.TestCase):

    def test(self):
        project_manager = ProjectManager("unit_tests")
        #project_manager.create_project_from_biom(biom_name="table.biom", subsample_type="auto")


    def test__decompose_silva_taxonomy(self):
        project_manager = ProjectManager("unit_tests")
        expected_output = ["Bacteria", "Bacteroidetes", "Flavobacteria", "Flavobacteriales", "Flavobacteriaceae", "Chryseobacterium", "meningosepticum"]
        actual_output = project_manager.process_taxonomy_line("Silva",
                                                              "Bacteria(100);\"Bacteroidetes\"(100);Flavobacteria(100);\"Flavobacteriales\"(100);Flavobacteriaceae(100);Chryseobacterium(100);meningosepticum(100)")
        self.assertEquals(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Silva",
                                                              "Bacteria;Bacteroidetes;Flavobacteria;Flavobacteriales;Flavobacteriaceae;Chryseobacterium;meningosepticum")
        self.assertEquals(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Silva",
                                                              ["Bacteria(100)", "Bacteroidetes", "Flavobacteria[98]",
                                                               "Flavobacteriales", "Flavobacteriaceae",
                                                               "[100]Chryseobacterium", "meningosepticum"])
        self.assertEquals(expected_output, actual_output)


    def test__decompose_gg_taxonomy(self):
        project_manager = ProjectManager("unit_tests")
        expected_output = ["Bacteria", "Bacteroidetes", "Flavobacteria", "Flavobacteria", "Flavobacteriaceae", "Chryseobacterium", "meningosepticum"]
        actual_output = project_manager.process_taxonomy_line("Greengenes",
                                                              "k__Bacteria(100);\"p__Bacteroidetes\"(100);c__Flavobacteria(100);\"o__Flavobacteria\"(100);f__Flavobacteriaceae(100);g__Chryseobacterium(100);s__meningosepticum(100)")
        self.assertEquals(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Greengenes",
                                                              "k__Bacteria;p__Bacteroidetes;c__Flavobacteria;o__Flavobacteria;f__Flavobacteriaceae;g__Chryseobacterium;s__meningosepticum")
        self.assertEquals(expected_output, actual_output)

        actual_output = project_manager.process_taxonomy_line("Greengenes",
                                                              ["k__Bacteria(100)", "p__Bacteroidetes", "c__Flavobacteria[98]",
                                                               "o__Flavobacteria", "f__Flavobacteriaceae",
                                                               "[100]g__Chryseobacterium", "s__meningosepticum"])
        self.assertEquals(expected_output, actual_output)

if __name__ == '__main__':
    unittest.main()