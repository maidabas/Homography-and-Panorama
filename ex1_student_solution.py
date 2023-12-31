"""Projective Homography and Panorama Solution."""
import numpy as np

from typing import Tuple
from random import sample
from collections import namedtuple

from numpy.linalg import svd
from scipy.interpolate import griddata

PadStruct = namedtuple('PadStruct',
                       ['pad_up', 'pad_down', 'pad_right', 'pad_left'])


class Solution:
    """Implement Projective Homography and Panorama Solution."""

    def __init__(self):
        pass

    @staticmethod
    def compute_homography_naive(match_p_src: np.ndarray,
                                 match_p_dst: np.ndarray) -> np.ndarray:
        """Compute a Homography in the Naive approach, using SVD decomposition.

        Args:
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.

        Returns:
            Homography from source to destination, 3x3 numpy array.
        """
        # return homography

        # Given - N matching points - meaning 2N rows in homography matrix (each row per x/y in each point)
        N = match_p_src.shape[1]
        A = []
        for i in range(N):
            row1 = [-match_p_src[0, i], -match_p_src[1, i], -1, 0, 0, 0, match_p_src[0, i] * match_p_dst[0, i],
                    match_p_src[1, i] * match_p_dst[0, i], match_p_dst[0, i]]
            row2 = [0, 0, 0, -match_p_src[0, i], -match_p_src[1, i], -1, match_p_src[0, i] * match_p_dst[1, i],
                    match_p_src[1, i] * match_p_dst[1, i], match_p_dst[1, i]]
            A.append(row1)
            A.append(row2)
        # Find eigenvalues using SVD process and choose the last eigenvalue as the holography matrix parameters
        u, s, vh = np.linalg.svd(A, full_matrices=True)
        # Take last vector in vh and reshape it to be 3 x 3:
        homography = vh[-1:, ].reshape((3, 3))
        return homography

    @staticmethod
    def compute_forward_homography_slow(
            homography: np.ndarray,
            src_image: np.ndarray,
            dst_image_shape: tuple = (1088, 1452, 3)) -> np.ndarray:
        """Compute a Forward-Homography in the Naive approach, using loops.

        Iterate over the rows and columns of the source image, and compute
        the corresponding point in the destination image using the
        projective homography. Place each pixel value from the source image
        to its corresponding location in the destination image.
        Don't forget to round the pixel locations computed using the
        homography.

        Args:
            homography: 3x3 Projective Homography matrix.
            src_image: HxWx3 source image.
            dst_image_shape: tuple of length 3 indicating the destination
            image height, width and color dimensions.

        Returns:
            The forward homography of the source image to its destination.
        """
        # return new_image
        target_image = np.zeros(shape=dst_image_shape)
        for i in range(src_image.shape[0]):
            for j in range(src_image.shape[1]):
                new_coor = np.matmul(homography, [j, i, 1])
                u = np.round(new_coor[0] / new_coor[2]).astype(int)
                v = np.round(new_coor[1] / new_coor[2]).astype(int)
                if dst_image_shape[0] > v >= 0 and dst_image_shape[1] > u >= 0:
                    target_image[v, u, :] = src_image[i, j, :] / 255.0
        return target_image

    @staticmethod
    def compute_forward_homography_fast(
            homography: np.ndarray,
            src_image: np.ndarray,
            dst_image_shape: tuple = (1088, 1452, 3)) -> np.ndarray:
        """Compute a Forward-Homography in a fast approach, WITHOUT loops.

        (1) Create a meshgrid of columns and rows.
        (2) Generate a matrix of size 3x(H*W) which stores the pixel locations
        in homogeneous coordinates.
        (3) Transform the source homogeneous coordinates to the target
        homogeneous coordinates with a simple matrix multiplication and
        apply the normalization you've seen in class.
        (4) Convert the coordinates into integer values and clip them
        according to the destination image size.
        (5) Plant the pixels from the source image to the target image according
        to the coordinates you found.

        Args:
            homography: 3x3 Projective Homography matrix.
            src_image: HxWx3 source image.
            dst_image_shape: tuple of length 3 indicating the destination.
            image height, width and color dimensions.

        Returns:
            The forward homography of the source image to its destination.
        """
        # return new_image
        target_image = np.zeros(shape=dst_image_shape)

        # (1) Create a meshgrid of columns and rows.
        H = src_image.shape[0]
        W = src_image.shape[1]
        yv, xv = np.meshgrid(np.arange(W), np.arange(H), indexing='ij')
        # (2) Generate a matrix of size 3x(H*W) which stores the pixel locations in homogeneous coordinates.
        coor_matrix = np.ones((3, H * W), dtype=int)
        coor_matrix[0, :] = yv.flatten()
        coor_matrix[1, :] = xv.flatten()
        src_row0 = coor_matrix[0, :]
        src_row1 = coor_matrix[1, :]
        # (3) Transform the source homogeneous coordinates to the target homogeneous coordinates
        new_coor = np.matmul(homography, coor_matrix)
        # (4) normalization + round + clip
        new_coor = np.round(new_coor / new_coor[2, :]).astype(int)
        temp_row0 = new_coor[0, :]
        temp_row1 = new_coor[1, :]
        cond1 = np.logical_and(temp_row0 < dst_image_shape[1], temp_row0 >= 0)  # within image bounds
        cond2 = np.logical_and(temp_row1 < dst_image_shape[0], temp_row1 >= 0)  # within image bounds
        cond = np.logical_and(cond1, cond2)
        # (5) Plant the pixels from the source image to the target image
        target_image[temp_row1[cond == True], temp_row0[cond == True]] = src_image[src_row1[cond == True], src_row0[
            cond == True]] / 255.0
        return target_image

    @staticmethod
    def test_homography(homography: np.ndarray,
                        match_p_src: np.ndarray,
                        match_p_dst: np.ndarray,
                        max_err: float) -> Tuple[float, float]:
        """Calculate the quality of the projective transformation model.

        Args:
            homography: 3x3 Projective Homography matrix.
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            max_err: A scalar that represents the maximum distance (in
            pixels) between the mapped src point to its corresponding dst
            point, in order to be considered as valid inlier.

        Returns:
            A tuple containing the following metrics to quantify the
            homography performance:
            fit_percent: The probability (between 0 and 1) validly mapped src
            points (inliers).
            dist_mse: Mean square error of the distances between validly
            mapped src points, to their corresponding dst points (only for
            inliers). In edge case where the number of inliers is zero,
            return dist_mse = 10 ** 9.
        """
        # return fit_percent, dist_mse
        # compute forward mapping of source points
        src_mapping = np.matmul(homography, np.vstack([match_p_src, np.ones(match_p_src.shape[1])]))  # add row of ones
        new_coor = src_mapping / src_mapping[2, :]  # normalize
        match_p_src_mapped = new_coor[:2, :]  # remove row of ones
        # compare to matching destination points (using euclidean distance)
        dist = np.array(
            [np.linalg.norm(match_p_dst[:, i] - match_p_src_mapped[:, i]) for i in range(match_p_dst.shape[1])])
        inliers = (dist <= max_err)

        if sum(inliers) == 0:
            dist_mse = 10 ** 9
        else:
            # calc mse only for inliers only
            dist_mse = np.square(np.subtract(match_p_dst[:, inliers], match_p_src_mapped[:, inliers])).mean()
        # calc probability of an inlier
        fit_percent = inliers.sum() / match_p_src.shape[1]
        return (fit_percent, dist_mse)

    @staticmethod
    def meet_the_model_points(homography: np.ndarray,
                              match_p_src: np.ndarray,
                              match_p_dst: np.ndarray,
                              max_err: float) -> Tuple[np.ndarray, np.ndarray]:
        """Return which matching points meet the homography.

        Loop through the matching points, and return the matching points from
        both images that are inliers for the given homography.

        Args:
            homography: 3x3 Projective Homography matrix.
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            max_err: A scalar that represents the maximum distance (in
            pixels) between the mapped src point to its corresponding dst
            point, in order to be considered as valid inlier.
        Returns:
            A tuple containing two numpy nd-arrays, containing the matching
            points which meet the model (the homography). The first entry in
            the tuple is the matching points from the source image. That is a
            nd-array of size 2xD (D=the number of points which meet the model).
            The second entry is the matching points form the destination
            image (shape 2xD; D as above).
        """

        """INSERT YOUR CODE HERE"""
        # perform forward mapping of source image
        src_mapping = np.matmul(homography, np.vstack([match_p_src, np.ones(match_p_src.shape[1])]))  # add row of ones
        new_coor = src_mapping / src_mapping[2, :]  # normalize
        match_p_src_mapped = new_coor[:2, :]  # remove row of ones   

        # compare to matching destination points (using euclidean distance)
        dist = np.array(
            [np.linalg.norm(match_p_dst[:, i] - match_p_src_mapped[:, i]) for i in range(match_p_dst.shape[1])])
        inliers = (dist <= max_err)

        mp_src_meets_model = match_p_src[:, inliers]  # extract inlier src points
        mp_dst_meets_model = match_p_dst[:, inliers]  # extract inlier dst points

        return mp_src_meets_model, mp_dst_meets_model

    def compute_homography(self,
                           match_p_src: np.ndarray,
                           match_p_dst: np.ndarray,
                           inliers_percent: float,
                           max_err: float) -> np.ndarray:
        """Compute homography coefficients using RANSAC to overcome outliers.

        Args:
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            inliers_percent: The expected probability (between 0 and 1) of
            correct match points from the entire list of match points.
            max_err: A scalar that represents the maximum distance (in
            pixels) between the mapped src point to its corresponding dst
            point, in order to be considered as valid inlier.
        Returns:
            homography: Projective transformation matrix from src to dst.
        """
        # # use class notations:
        # w = inliers_percent
        # # t = max_err
        # # p = parameter determining the probability of the algorithm to
        # # succeed
        # p = 0.99
        # # the minimal probability of points which meets with the model
        # d = 0.5
        # # number of points sufficient to compute the model
        # n = 4
        # # number of RANSAC iterations (+1 to avoid the case where w=1)
        # k = int(np.ceil(np.log(1 - p) / np.log(1 - w ** n))) + 1
        # return homography
        """INSERT YOUR CODE HERE"""

        # Define class notations
        w = inliers_percent
        t = max_err
        p = 0.99  # probability of the algorithm to secceed
        d = 0.5  # minimal probability of points which meets the model
        n = 4  # number of points sufficient to compute the model
        k = int(np.ceil(np.log(1 - p) / np.log(1 - w ** n))) + 1  # no. of iterations (+1)
        err = np.inf  # stores the model error
        # loop over number of iterations
        for i in range(k):
            # randomly select n points
            choose_index = np.random.choice(match_p_src.shape[1], size=n, replace=False)
            chosen_p_src = match_p_src[:, choose_index]
            chosen_p_dst = match_p_dst[:, choose_index]

            # compute homography based on chosen points (using the )
            homography_test = self.compute_homography_naive(chosen_p_src, chosen_p_dst)

            # Find inliers
            inliers_src, inliers_dst = self.meet_the_model_points(homography_test,
                                                                  match_p_src,
                                                                  match_p_dst,
                                                                  max_err=t)

            # Check d condition
            if inliers_src.shape[1] / match_p_src.shape[1] > d:
                # re-compute model using all founded inliers
                homography_inliers = self.compute_homography_naive(inliers_src, inliers_dst)
                # compute model error
                _, model_err = self.test_homography(homography_inliers, match_p_src, match_p_dst, t)
                # check if the model has improved from last iteration
                if model_err < err:
                    # if so - store the error and the model
                    err = model_err
                    homography = homography_inliers
        if err >= np.inf:
            return ("High error, model wasn't saved")
        return homography

    @staticmethod
    def compute_backward_mapping(
            backward_projective_homography: np.ndarray,
            src_image: np.ndarray,
            dst_image_shape: tuple = (1088, 1452, 3)) -> np.ndarray:
        """Compute backward mapping.

        (1) Create a mesh-grid of columns and rows of the destination image.
        (2) Create a set of homogenous coordinates for the destination image
        using the mesh-grid from (1).
        (3) Compute the corresponding coordinates in the source image using
        the backward projective homography.
        (4) Create the mesh-grid of source image coordinates.
        (5) For each color channel (RGB): Use scipy's interpolation.griddata
        with an appropriate configuration to compute the bi-cubic
        interpolation of the projected coordinates.

        Args:
            backward_projective_homography: 3x3 Projective Homography matrix.
            src_image: HxWx3 source image.
            dst_image_shape: tuple of length 3 indicating the destination shape.

        Returns:
            The source image backward warped to the destination coordinates.
        """

        # return backward_warp
        """INSERT YOUR CODE HERE"""
        # 1. create a meshgrid of shape of the dst image:
        yv, xv = np.meshgrid(np.arange(dst_image_shape[1]), np.arange(dst_image_shape[0]))
        # 2. create a set of homogenous coordinates
        coor_matrix = np.ones((3, dst_image_shape[0] * dst_image_shape[1]))
        coor_matrix[0, :] = yv.flatten()
        coor_matrix[1, :] = xv.flatten()
        coor_matrix = coor_matrix.astype(int)
        # 3. Compute the corresponding coordinates in the source image using
        # the backward projective homography
        new_coor = np.matmul(backward_projective_homography, coor_matrix)
        # normalize:
        new_coor = new_coor / new_coor[2, :]
        pixel_locs_dst = np.transpose([new_coor[1, :], new_coor[0, :]])
        # 4. create meshgrid of source image
        yv_src, xv_src = np.meshgrid(np.arange(src_image.shape[1]), np.arange(src_image.shape[0]))
        # get image values in pixel locations in source image
        xv_src = xv_src.flatten().astype(int)
        yv_src = yv_src.flatten().astype(int)
        pixel_values = src_image[xv_src, yv_src]
        pixel_locs_src = np.transpose([xv_src, yv_src])
        # 5. compute interpolation for black points
        new_image = griddata(pixel_locs_src, pixel_values, pixel_locs_dst, method='cubic', fill_value=0).astype(int)
        new_image = np.reshape(new_image, dst_image_shape)
        new_image = np.clip(new_image, 0, 255).astype(np.uint8)
        return new_image

    @staticmethod
    def find_panorama_shape(src_image: np.ndarray,
                            dst_image: np.ndarray,
                            homography: np.ndarray
                            ) -> Tuple[int, int, PadStruct]:
        """Compute the panorama shape and the padding in each axes.

        Args:
            src_image: Source image expected to undergo projective
            transformation.
            dst_image: Destination image to which the source image is being
            mapped to.
            homography: 3x3 Projective Homography matrix.

        For each image we define a struct containing it's corners.
        For the source image we compute the projective transformation of the
        coordinates. If some of the transformed image corners yield negative
        indices - the resulting panorama should be padded with at least
        this absolute amount of pixels.
        The panorama's shape should be:
        dst shape + |the largest negative index in the transformed src index|.

        Returns:
            The panorama shape and a struct holding the padding in each axes (
            row, col).
            panorama_rows_num: The number of rows in the panorama of src to dst.
            panorama_cols_num: The number of columns in the panorama of src to
            dst.
            padStruct = a struct with the padding measures along each axes
            (row,col).
        """
        src_rows_num, src_cols_num, _ = src_image.shape
        dst_rows_num, dst_cols_num, _ = dst_image.shape
        src_edges = {}
        src_edges['upper left corner'] = np.array([1, 1, 1])
        src_edges['upper right corner'] = np.array([src_cols_num, 1, 1])
        src_edges['lower left corner'] = np.array([1, src_rows_num, 1])
        src_edges['lower right corner'] = \
            np.array([src_cols_num, src_rows_num, 1])
        transformed_edges = {}
        for corner_name, corner_location in src_edges.items():
            transformed_edges[corner_name] = homography @ corner_location
            transformed_edges[corner_name] /= transformed_edges[corner_name][-1]
        pad_up = pad_down = pad_right = pad_left = 0
        for corner_name, corner_location in transformed_edges.items():
            if corner_location[1] < 1:
                # pad up
                pad_up = max([pad_up, abs(corner_location[1])])
            if corner_location[0] > dst_cols_num:
                # pad right
                pad_right = max([pad_right,
                                 corner_location[0] - dst_cols_num])
            if corner_location[0] < 1:
                # pad left
                pad_left = max([pad_left, abs(corner_location[0])])
            if corner_location[1] > dst_rows_num:
                # pad down
                pad_down = max([pad_down,
                                corner_location[1] - dst_rows_num])
        panorama_cols_num = int(dst_cols_num + pad_right + pad_left)
        panorama_rows_num = int(dst_rows_num + pad_up + pad_down)
        pad_struct = PadStruct(pad_up=int(pad_up),
                               pad_down=int(pad_down),
                               pad_left=int(pad_left),
                               pad_right=int(pad_right))
        return panorama_rows_num, panorama_cols_num, pad_struct

    @staticmethod
    def add_translation_to_backward_homography(backward_homography: np.ndarray,
                                               pad_left: int,
                                               pad_up: int) -> np.ndarray:
        """Create a new homography which takes translation into account.

        Args:
            backward_homography: 3x3 Projective Homography matrix.
            pad_left: number of pixels that pad the destination image with
            zeros from left.
            pad_up: number of pixels that pad the destination image with
            zeros from the top.

        (1) Build the translation matrix from the pads.
        (2) Compose the backward homography and the translation matrix together.
        (3) Scale the homography as learnt in class.

        Returns:
            A new homography which includes the backward homography and the
            translation.
        """
        # return final_homography
        """INSERT YOUR CODE HERE"""
        # 1. Build the translation matrix: [[1, 0, dx], [0, 1, dy], [0, 0, 1]]
        trans_matrix = np.array([[1, 0, -pad_left], [0, 1, -pad_up], [0, 0, 1]])
        norm_trans_matrix = np.multiply(1 / np.linalg.norm(trans_matrix), trans_matrix)
        # 2. compose the translation and the homography matrix together
        homography = np.matmul(backward_homography, norm_trans_matrix)
        homography = np.multiply(1 / np.linalg.norm(homography), homography)
        return homography

    def panorama(self,
                 src_image: np.ndarray,
                 dst_image: np.ndarray,
                 match_p_src: np.ndarray,
                 match_p_dst: np.ndarray,
                 inliers_percent: float,
                 max_err: float) -> np.ndarray:
        """Produces a panorama image from two images, and two lists of
        matching points, that deal with outliers using RANSAC.

        (1) Compute the forward homography and the panorama shape.
        (2) Compute the backward homography.
        (3) Add the appropriate translation to the homography so that the
        source image will plant in place.
        (4) Compute the backward warping with the appropriate translation.
        (5) Create the an empty panorama image and plant there the
        destination image.
        (6) place the backward warped image in the indices where the panorama
        image is zero.
        (7) Don't forget to clip the values of the image to [0, 255].


        Args:
            src_image: Source image expected to undergo projective
            transformation.
            dst_image: Destination image to which the source image is being
            mapped to.
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            inliers_percent: The expected probability (between 0 and 1) of
            correct match points from the entire list of match points.
            max_err: A scalar that represents the maximum distance (in pixels)
            between the mapped src point to its corresponding dst point,
            in order to be considered as valid inlier.

        Returns:
            A panorama image.

        """
        # return np.clip(img_panorama, 0, 255).astype(np.uint8)
        """INSERT YOUR CODE HERE"""

        # 1. compute forward homography src -> dst
        forward_homography = self.compute_homography(match_p_src,
                                                     match_p_dst,
                                                     inliers_percent,
                                                     max_err)
        # compute panorama shape
        panorama_rows_num, panorama_cols_num, pad_struct = self.find_panorama_shape(src_image,
                                                                                    dst_image,
                                                                                    forward_homography)
        # 2. compute backward homography dst -> src
        backward_homography = np.linalg.inv(forward_homography)

        # 3. add the appropriate translation
        pad_left = pad_struct.pad_left
        pad_up = pad_struct.pad_up
        translated_homography = self.add_translation_to_backward_homography(backward_homography, pad_left, pad_up)

        # Create empty panorama image
        panorama_empty = np.zeros((panorama_rows_num,
                                   panorama_cols_num, 3))
        # plant the dst image in the panorama
        panorama_empty[pad_up:pad_up+dst_image.shape[0], pad_left:pad_left+dst_image.shape[1], :] = dst_image

        # compute backward image
        backward_image = self.compute_backward_mapping(translated_homography, src_image,
                                                       (panorama_empty.shape[0], panorama_empty.shape[1], 3))

        # plant the backward image in the panorama
        img_panorama = np.where(panorama_empty.round() == 0, backward_image, panorama_empty)

        return np.clip(img_panorama, 0, 255).astype(np.uint8)
