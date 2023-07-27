# CV_assignment_1

In this project, we implement Projective Homography and Panorama Solution.

Homography is computed in different methods:
## 1. Naive approach using SVD decomposition

In the naive approach: 
- a projective homography matrix is generated
- using chosen points in the source image and the destination image, a forward naive algorithm is used to create the projected image. The forward algorithm can be applied using loops (slow method) or using meshgrids (fast method).

The projective transformation is then tested by calculating its quality. 
N matching points are sampled from the source and destination images, and the MSE of the distances between the source points to the corresponding destination points is calculated. Outliers detection is done before this process, in order to ommit outliers and perform this check on inliers only. 


## 2. RANSAC approach

In order to deal with outliers, RANSAC algorith is applied to create a better panorama and choose the matching points more properly. 

In addition to forward mapping a backward mapping is also executed (from destination image to source image) in order to clean noise from the destination image and create a smoother output image. 

## Panorama creation

The panorama image is then created by applying the following steps:
1. Computing the forward homography (from source image to destination image) and the final panorama shape (image size)
2. Computing the backward homography (from destination image to source image)
3. Adding the appropriate translation to the homography so that the source image will plant in place
4. Computing the backward wrapping with the appropriate translation
5. Creating an empty panorama image with the generate size and plant there the destination image
6. Placing the backward wraped image in the indices where the panorama image is zero.
7. In order to create an actual image, clipping the image values to [0, 255]
