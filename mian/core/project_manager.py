# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#

import uuid

from io import StringIO
from mian.core.otu_table_subsampler import OTUTableSubsampler
from mian.core.constants import RAW_OTU_TABLE_FILENAME, \
    SUBSAMPLED_OTU_TABLE_FILENAME, BIOM_FILENAME, TAXONOMY_FILENAME, SAMPLE_METADATA_FILENAME
import csv
import os
import re
import logging
from biom import load_table

from mian.model.map import Map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectManager(object):

    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def __init__(self, user_id):
        self.user_id = user_id

    def create_project_from_tsv(self, project_name, otu_filename, taxonomy_filename, sample_metadata_filename, subsample_type="auto", subsample_to=0):

        # Creates a directory for this project
        pid = str(uuid.uuid4())
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        else:
            raise Exception("Cannot create project folder as it already exists")

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        os.rename(os.path.join(user_staging_dir, otu_filename), os.path.join(project_dir, RAW_OTU_TABLE_FILENAME))
        os.rename(os.path.join(user_staging_dir, taxonomy_filename), os.path.join(project_dir, TAXONOMY_FILENAME))
        os.rename(os.path.join(user_staging_dir, sample_metadata_filename), os.path.join(project_dir, SAMPLE_METADATA_FILENAME))

        # Subsamples raw OTU table
        subsample_value, otus_removed = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                    pid=pid,
                                                                    subsample_type=subsample_type,
                                                                    manual_subsample_to=subsample_to,
                                                                    raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                    output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        # Creates map.txt file
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.orig_otu_table_name = otu_filename
        map_file.orig_sample_metadata_name = sample_metadata_filename
        map_file.orig_taxonomy_name = taxonomy_filename
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.save()

        return pid

    def create_project_from_biom(self, project_name, biom_name, subsample_type="auto", subsample_to=0):
        """
        Reads a .biom from a provided file location and converts it into a mian-compatible TSV file

        """

        # Creates a directory for this project
        pid = str(uuid.uuid4())
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        else:
            raise Exception("Cannot create project folder as it already exists")

        pid, sub = self.__process_biom_file(pid, project_dir, project_name, biom_name, subsample_type, subsample_to)
        return pid

    def __process_biom_file(self, pid, project_dir, project_name, biom_name, subsample_type="auto", subsample_to=0):
        # Renames the uploaded file to a standard file schema and moves to the project directory
        biom_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        biom_staging_dir = os.path.join(biom_staging_dir, biom_name)
        biom_project_dir = os.path.join(project_dir, BIOM_FILENAME)
        os.rename(biom_staging_dir, biom_project_dir)
        logger.info("Moved " + str(biom_staging_dir) + " to " + str(biom_project_dir))

        # Extracts the OTU table from the biom file and saves the raw OTU file
        biom_path = os.path.join(project_dir, BIOM_FILENAME)
        raw_table_path = os.path.join(project_dir, RAW_OTU_TABLE_FILENAME)

        logger.info("Converting biom to intermediate TSV file " + biom_path)
        table = load_table(biom_path)
        self.__save_biom_table_as_tsv(table, raw_table_path)

        # Subsamples the raw OTU file
        subsample_to, removed_otus = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                            pid=pid,
                                                                            subsample_type=subsample_type,
                                                                            manual_subsample_to=subsample_to,
                                                                            raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                            output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        # Create Sample Metadata File
        logger.info("Creating sample metadata file")
        sample_metadata_path = os.path.join(project_dir, SAMPLE_METADATA_FILENAME)
        sample_metadata = table.metadata(None, 'sample')
        sample_ids = table.ids('sample')
        with open(sample_metadata_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            sample_index = 0
            for k in sample_metadata:
                if sample_index == 0:
                    # We will write out the metadata headers at the top of this file
                    headers = ["SampleID"]
                    for key, value in sorted(k.items()):
                        headers.append(key)
                    output_tsv.writerow(headers)

                sample_id = sample_ids[sample_index]
                row_data = [sample_id]
                for key, value in sorted(k.items()):
                    # Write out the contents of each metadata
                    row_data.append(value)
                output_tsv.writerow(row_data)
                sample_index += 1

        # Generates Taxonomy File
        logger.info("Creating taxonomy file")
        otu_metadata = table.metadata(None, 'observation')
        otu_ids = table.ids('observation')
        otu_metadata_path = os.path.join(project_dir, TAXONOMY_FILENAME)
        taxonomy_type = ""
        with open(otu_metadata_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            otu_index = 0
            taxonomy_key = ""

            # Each row in the otu_metadata is the metadata for the corresponding OTU
            for k in otu_metadata:
                if otu_index == 0:
                    # Do some additional processing for the first OTU metadata line processed
                    logger.info("Processing first OTU metadata / taxonomy header line")

                    # We will write out the metadata headers at the top of this file
                    headers = ["OTU"]

                    # Find which column is the taxonomy column
                    # Logic:
                    #    1) Look for the metadata key which says "taxonomy"
                    #    2) If (1) does not work, look into the metadata value to find one that contains "Bacteria"
                    #       as this is common to both Silva and Greengenes taxonomy

                    logger.info("Finding taxonomy key %s", str(k))

                    potential_taxonomy_key = ""
                    for key, value in k.items():
                        if key.lower() == "taxonomy":
                            taxonomy_key = key
                            break
                        elif (type(value) is list and any("bacteria" in s.lower() for s in value)) or \
                                (type(value) is str and "bacteria" in value.lower()):
                            potential_taxonomy_key = key

                    if taxonomy_key == "":
                        logger.info("Using the potential taxonomy key of " + str(potential_taxonomy_key) +
                                    " because could not find the actual taxonomy key")
                        taxonomy_key = potential_taxonomy_key

                    if taxonomy_key == "":
                        logger.error("No taxonomy found!")
                        raise ValueError("No taxonomy found!")

                    taxonomy_type = self.get_taxonomy_type(k[taxonomy_key])
                    logger.info("Taxonomy type was determined to be %s", taxonomy_type)

                    headers.append(taxonomy_key)

                    for key, value in sorted(k.items()):
                        if key != taxonomy_key:
                            headers.append(key)
                    output_tsv.writerow(headers)

                # Write out the taxonomy file line by line such that the taxonomy is always the second column
                # We keep the other OTU metadata just in case we will use it in the future
                otu_id = otu_ids[otu_index]
                if otu_id not in removed_otus:
                    row_data = [otu_id] + self.process_taxonomy_line(taxonomy_type, k[taxonomy_key])
                    logger.info("Row data generated: " + str(row_data))
                    for key, value in sorted(k.items()):
                        if key != taxonomy_key:
                            row_data.append(value)
                    output_tsv.writerow(row_data)
                otu_index += 1

        # Creates map.txt file
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.orig_biom_name = biom_name
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_to
        map_file.taxonomy_type = taxonomy_type
        map_file.save()

        return pid, subsample_to

    def __save_biom_table_as_tsv(self, table, output_path):
        result = table.to_tsv(header_key="",
                              header_value="",
                              metadata_formatter="sc_separated")

        # Converts the TSV string to an array
        f = StringIO(result)
        intermediate_table = []
        base_csv = csv.reader(f, delimiter='\t', quotechar='|')
        for o in base_csv:
            if len(o) > 1:
                intermediate_table.append(o)

        # The intermediate table is sample-columnar (ie. rows are OTUs) but the majority of the analysis in
        # mian uses samples as rows so we perform a conversion
        with open(output_path, 'w') as out_f:
            output_tsv = csv.writer(out_f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for x in zip(*intermediate_table):
                output_tsv.writerow(x)

        logger.info("Finished transposing to final TSV file " + output_path)

    def get_taxonomy_type(self, taxonomy_line):
        if type(taxonomy_line) is list:
            if any("k__" in s.lower() for s in taxonomy_line):
                return "Greengenes"
            else:
                return "Silva"
        else:
            if "k__" in taxonomy_line:
                return "Greengenes"
            else:
                return "Silva"

    def process_taxonomy_line(self, taxonomy_type, taxonomy_line):
        if taxonomy_type == "Greengenes":
            return self.__decompose_gg_taxonomy(taxonomy_line)
        else:
            return self.__decompose_silva_taxonomy(taxonomy_line)

    def __decompose_silva_taxonomy(self, taxonomy_arg):
        # IPF OTU Map
        # Bacteria(100);"Bacteroidetes"(100);Flavobacteria(100);"Flavobacteriales"(100);Flavobacteriaceae(100);Chryseobacterium(100);
        # ["Bacteria", "Bacteroidetes"]

        taxonomy_line = taxonomy_arg
        if type(taxonomy_arg) is list:
            # Creates a semi-colon delimited string for consistent processing below
            taxonomy_line = ";".join(taxonomy_arg)
        elif taxonomy_arg.startswith("["):
            taxonomy_line = taxonomy_arg[1:-1]
            taxonomy_line = taxonomy_line.replace(",", ";")

        taxonomy_line = taxonomy_line.strip()

        taxonomy_line = taxonomy_line.replace("\"", "")

        invalid_pattern = re.compile("(\(\d*?\))|(\[\d*?\])")
        taxonomy_line = re.sub(invalid_pattern, "", taxonomy_line)

        decomposed = taxonomy_line.split(";")

        # Pad the array until the desired classification depth is achieved
        while len(decomposed) < 7:
            decomposed.append("")

        return decomposed

    def __decompose_gg_taxonomy(self, taxonomy_arg):
        # k__Bacteria;p__Bacteroidetes;c__Bacteroidia;o__Bacteroidales;f__[Paraprevotellaceae];
        # k__Bacteria;p__Bacteroidetes;c__Bacteroidia;o__Bacteroidales;f__Prevotellaceae;g__Prevotella;
        # ['k__Bacteria', 'p__Firmicutes', 'c__Clostridia', 'o__Halanaerobiales', 'f__Halanaerobiaceae', 'g__Halanaerobium', 's__Halanaerobiumsaccharolyticum']
        # Root;k__Bacteria;p__Firmicutes;c__Clostridia;o__Clostridiales;f__Lachnospiraceae

        taxonomy_line = taxonomy_arg
        if type(taxonomy_arg) is list:
            # Creates a semi-colon delimited string for consistent processing below
            taxonomy_line = ";".join(taxonomy_arg)
        elif taxonomy_arg.startswith("["):
            taxonomy_line = taxonomy_arg[1:-1]
            taxonomy_line = taxonomy_line.replace(",", ";")

        taxonomy_line = taxonomy_line.strip()

        taxonomy_line = taxonomy_line.replace("\"", "")

        if taxonomy_line.startswith("Root;") or taxonomy_line.startswith("root;"):
            taxonomy_line = taxonomy_line[5:]

        invalid_pattern = re.compile("(\(\d*?\))|(\[\d*?\])")
        taxonomy_line = re.sub(invalid_pattern, "", taxonomy_line)

        arr = taxonomy_line.split(";")
        decomposed = []
        for tax in arr:
            if tax.lower() == "root":
                continue
            else:
                gg_tax_item = tax
                if "__" in tax:
                    gg_tax_item = tax.split("__")[1]
                decomposed.append(gg_tax_item)

        # Pad the array until the desired classification depth is achieved
        while len(decomposed) < 7:
            decomposed.append("")

        return decomposed

    def modify_subsampling(self, pid, subsample_type="auto", subsample_to=0):
        # Subsamples raw OTU table
        subsample_value, otus_removed = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                    pid=pid,
                                                                    subsample_type=subsample_type,
                                                                    manual_subsample_to=subsample_to,
                                                                    raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                    output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        # Updates the map.txt file
        map_file = Map(self.user_id, pid)
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.save()

        return subsample_value

    def update_project_from_tsv(self, pid, otu_filename, taxonomy_filename, sample_metadata_filename):

        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)

        map_file = Map(self.user_id, pid)

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        if otu_filename is not None:
            os.rename(os.path.join(user_staging_dir, otu_filename), os.path.join(project_dir, RAW_OTU_TABLE_FILENAME))
        if taxonomy_filename is not None:
            os.rename(os.path.join(user_staging_dir, taxonomy_filename), os.path.join(project_dir, TAXONOMY_FILENAME))
        if sample_metadata_filename is not None:
            os.rename(os.path.join(user_staging_dir, sample_metadata_filename), os.path.join(project_dir, SAMPLE_METADATA_FILENAME))

        # Subsamples raw OTU table
        if otu_filename is not None:
            subsample_value, otus_removed = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                        pid=pid,
                                                                        subsample_type=map_file.subsampled_type,
                                                                        manual_subsample_to=map_file.subsampled_value,
                                                                        raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                        output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        if otu_filename is not None:
            map_file.orig_otu_table_name = otu_filename
        if sample_metadata_filename is not None:
            map_file.orig_sample_metadata_name = sample_metadata_filename
        if taxonomy_filename is not None:
            map_file.orig_taxonomy_name = taxonomy_filename
        map_file.save()

        return map_file.subsampled_value

    def update_project_from_biom(self, pid, biom_name):

        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)

        map_file = Map(self.user_id, pid)

        pid, subsample_value = self.__process_biom_file(pid, project_dir, map_file.project_name, biom_name, map_file.subsampled_type, map_file.subsampled_value)

        map_file.orig_biom_name = biom_name
        map_file.subsampled_value = subsample_value
        map_file.save()

        return subsample_value
