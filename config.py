#!/usr/bin/python3
import os

IMG_WIDTH = 1600
IMG_HEIGHT = 1200

OriginalImages = 'DATASET/original_images/images/'
OriginalMasks = 'DATASET/original_masks/masks/'

if not os.path.exists(OriginalImages):
    os.makedirs(OriginalImages)

if not os.path.exists(OriginalMasks):
    os.makedirs(OriginalMasks)

NewImages = 'DATASET/new_images/images/'
NewMasks = 'DATASET/new_masks/masks/'

if not os.path.exists(NewImages):
    os.makedirs(NewImages)

if not os.path.exists(NewMasks):
    os.makedirs(NewMasks)

# Temporary folder for the union of original and new images, final dataset that we are going to share is going to be in
# DATASET/train_val/{images, masks}_before_crop and DATASET/test/all_{images,masks}
AllImages = 'DATASET/all_images/images/'
AllMasks = 'DATASET/all_masks/masks/'

if not os.path.exists(AllImages):
    os.makedirs(AllImages)

if not os.path.exists(AllMasks):
    os.makedirs(AllMasks)

TrainValImages = 'DATASET/train_val/images_before_crop/images/'
TrainValMasks = 'DATASET/train_val/masks_before_crop/masks/'


if not os.path.exists(TrainValImages):
    os.makedirs(TrainValImages)

if not os.path.exists(TrainValMasks):
    os.makedirs(TrainValMasks)

TestImages = 'DATASET/test/all_images/images/'
TestMasks = 'DATASET/test/all_masks/masks/'

if not os.path.exists(TestImages):
    os.makedirs(TestImages)

if not os.path.exists(TestMasks):
    os.makedirs(TestMasks)

# Folder for all cropped images and masks
CropImages = 'DATASET/all_cropped_images/images/'
CropMasks = 'DATASET/all_cropped_masks/masks/'

if not os.path.exists(CropImages):
    os.makedirs(CropImages)

if not os.path.exists(CropMasks):
    os.makedirs(CropMasks)

# Final folder where the images for train reside, already cropped and augmented and weighted
# Cropped and augmented images are going to be read from the same folder
AugImages = 'DATASET/train_val/all_images/images/'
AugMasks = 'DATASET/train_val/all_masks/masks/'

if not os.path.exists(AugImages):
    os.makedirs(AugImages)

if not os.path.exists(AugMasks):
    os.makedirs(AugMasks)
