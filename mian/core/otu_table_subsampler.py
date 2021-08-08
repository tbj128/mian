# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#

from biom import Table
import numpy as np

from mian.core.data_io import DataIO
from mian.core.constants import SUBSAMPLE_TYPE_AUTO, SUBSAMPLE_TYPE_MANUAL, SUBSAMPLE_TYPE_DISABLED, \
    SUBSAMPLED_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME, SUBSAMPLE_TYPE_TSS, SUBSAMPLE_TYPE_CSS, \
    SUBSAMPLE_TYPE_UQ
import os
import logging
import scipy.sparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OTUTableSubsampler(object):

    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")

    @staticmethod
    def subsample_otu_table(subsample_type, manual_subsample_to, base, headers, sample_labels):
        """
        Subsamples the OTU table to the size of the smallest sample if subsample_to < 1. Otherwise, subsample
        the OTU table to the specified value
        :param subsample_type:
        :param subsample_to:
        :return:
        """

        if subsample_type == SUBSAMPLE_TYPE_AUTO:
            logger.info("Subsample type is auto")
            current_subsampled_depth = OTUTableSubsampler.__get_subsampled_depth(base)
            if current_subsampled_depth > -1:
                # Check if the table is already subsampled.
                # If so, we just need to copy the raw table to the subsampled table location
                logger.error("Table is already subsampled to a depth of " + str(current_subsampled_depth))
                return base, current_subsampled_depth, headers, sample_labels
            else:
                # Sums each sample row to find the row with the smallest sum
                # TODO: Bad input data may have very small row sum
                subsample_to = OTUTableSubsampler.__get_min_depth(base)
                return OTUTableSubsampler.__subsample_to_fixed(subsample_to, base, headers, sample_labels)

        elif subsample_type == SUBSAMPLE_TYPE_MANUAL:
            logger.info("Subsample type is manual")
            if str(manual_subsample_to).isdigit():
                subsample_to = int(manual_subsample_to)
                return OTUTableSubsampler.__subsample_to_fixed(subsample_to, base, headers, sample_labels)
            else:
                logger.error("Provided manual_subsample_to of " + str(manual_subsample_to) + " is not valid")
                raise ValueError("Provided subsample value is not valid")

        elif subsample_type == SUBSAMPLE_TYPE_TSS:
            # Implemented based on https://www.biorxiv.org/content/10.1101/406264v1.full
            logger.info("Subsample type is TSS")
            c = scipy.sparse.diags(1 / base.sum(axis=1).A.ravel())
            base = c @ base
            logger.info("Finished TSS subsampling")
            return base, 1, headers, sample_labels

        elif subsample_type == SUBSAMPLE_TYPE_UQ:
            logger.info("Subsample type is UQ")
            mat, headers = OTUTableSubsampler.upper_quantile_scaling(base.toarray(), headers)
            logger.info("Finished UQ subsampling")
            return scipy.sparse.csr_matrix(mat), 1, headers, sample_labels

        elif subsample_type == SUBSAMPLE_TYPE_CSS:
            logger.info("Subsample type is CSS")
            base = scipy.sparse.csr_matrix(OTUTableSubsampler.cumulative_sum_scaling(base.toarray()))
            logger.info("Finished CSS subsampling")
            return base, 1, headers, sample_labels

        elif subsample_type == SUBSAMPLE_TYPE_DISABLED:
            # Just copy the raw data table to the subsampled table location
            logger.info("Subsample type is disabled")
            return base, 0, headers, sample_labels
        else:
            logger.error("Invalid action selected")
            raise NotImplementedError("Invalid action selected")

    @staticmethod
    def __subsample_to_fixed(subsample_to, base, headers, sample_labels):
        temp_table = Table(base.transpose(), observation_ids=headers, sample_ids=sample_labels)
        temp_table = temp_table.subsample(subsample_to, axis="sample")
        subsampled_sample_labels = temp_table._sample_ids.tolist()
        subsampled_headers = temp_table._observation_ids.tolist()

        logger.info("Finished basic subsampling")

        return temp_table.matrix_data.transpose(), subsample_to, subsampled_headers, subsampled_sample_labels

    @staticmethod
    def __get_subsampled_depth(base):
        """
        Returns the depth that the table is subsampled to, or -1 if the table is not subsampled
        :param self:
        :param base:
        :return:
        """
        all_sum = base.sum(axis=1)
        if set(all_sum.A[:,0].tolist()) == 1:
            return all_sum.min().item()
        else:
            return -1

    @staticmethod
    def __get_min_depth(base):
        """
        Returns the sum of the row with the min sum
        :param self:
        :param base:
        :return:
        """
        return base.sum(axis=1).min().item()

    @staticmethod
    def __get_zero_columns(base):
        """
        Returns column indices which have sum of zero
        :param self:
        :param base:
        :return:
        """
        zero_columns = {}
        j = 0
        while j < len(base[0]):
            is_zero = True
            i = 0
            while i < len(base):
                if base[i][j] != 0:
                    is_zero = False
                    break
                i += 1
            if is_zero:
                zero_columns[j] = True
            j += 1
        return zero_columns

    @staticmethod
    def cumulative_sum_scaling(base, sl=1000):
        # Translated to Python from https://github.com/HCBravoLab/metagenomeSeq/blob/master/R/cumNormMat.R
        # Note that the original function assumed sample IDs were columns
        # where as here we assume sample IDs are rows instead

        # TODO: The code was translated assuming a dense matrix
        #       Look to natively support csr_matrices in the future
        x = base.transpose()
        p = OTUTableSubsampler.cum_norm_stat_fast(x)
        xx = x.astype('float')
        xx[xx == 0] = np.nan
        qs = np.nanquantile(xx, p, axis=0)
        newMat = []
        for i in range(xx.shape[1]):
            xx = x[:, i] - np.finfo(float).eps
            newMat.append(np.round(np.sum(xx[xx <= qs[i]])))
        newMat = np.array(newMat) / sl
        nmat = x.transpose() / newMat[:, None] # Take the transpose to apply "column" wise division
        # We purposefully do not take the transpose back since this is already in the right order
        # for our system (e.g. rows are sample IDs)
        return nmat

    @staticmethod
    def cum_norm_stat_fast(mat, rel=.1):
        # Translated to Python from https://github.com/HCBravoLab/metagenomeSeq/blob/df8a28214fa9cb25870dee0e5cc909c160ce8da2/R/cumNormStatFast.R
        # Like the original function, this assumes that mat contains sample IDs across the header
        smat_vals = []
        leng = 0
        for i in range(mat.shape[1]):
            # For each sample, get the indices sorted such that the non-zero values are first
            # print(f"1: {mat.shape}")
            args_non_zero = np.array(np.where(mat[:, i] > 0))[0]
            # print(f"2: {args_non_zero.shape}")
            raw_args_non_zero_sorted = np.squeeze(np.argsort(-mat[args_non_zero, i]))
            # print(f"3: {raw_args_non_zero_sorted.shape}")
            args_non_zero_sorted = args_non_zero[raw_args_non_zero_sorted.tolist()]
            # print(f"4: {args_non_zero_sorted.shape}")
            smat_vals.append(mat[args_non_zero_sorted, i])
            if len(args_non_zero_sorted) > leng:
                leng = len(args_non_zero_sorted)

        smat2 = np.empty((leng, mat.shape[1]))
        smat2.fill(np.nan)
        for i in range(mat.shape[1]):
            smat2[-len(smat_vals[i]):, i] = sorted(smat_vals[i])

        rmat2 = []
        for i in range(smat2.shape[1]):
            rmat2.append(np.nanquantile(smat2[:, i], q=np.linspace(0, 1, smat2.shape[0])))

        smat2 = np.nan_to_num(smat2)
        ref1 = np.mean(smat2, axis=1)
        ncols = len(rmat2)

        diffr = []
        for i in range(ncols):
            diffr.append(ref1 - rmat2[i])

        diffr = np.array(diffr).transpose()
        diffr1 = np.median(abs(diffr), axis=1)
        numerator = abs(np.diff(diffr1))
        denominator = diffr1[1:]
        x = (np.where((numerator / denominator) > rel)[0][0] + 1) / len(diffr1)
        print(f"Calculated x in cum_norm_stat_fast to be {x}")
        if x <= 0.50:
            print("Default value being used.")
            x = 0.50
        return x

    @staticmethod
    def upper_quantile_scaling(base, headers, q=0.75):
        mask = np.nonzero(np.sum(base, axis=0))[0]
        headers = np.array(headers)
        headers = headers[mask]
        base = base[:, mask]

        quantile_expressed = np.apply_along_axis(lambda v: np.quantile(v[np.nonzero(v)], q), 1, base)

        return (base / quantile_expressed[:, None]), headers
