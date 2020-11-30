#!/usr/bin/python3

IMG_WIDTH = 1600
IMG_HEIGTH = 1200

LoadImagesForCrop =  'DATA/TRAIN_VAL/all_images/images/'
LoadMasksForCrop = 'DATA/TRAIN_VAL/all_masks/masks/'
SaveCropImages =  'DATA/TRAIN_VAL/all_cropped_images/images/' 
SaveCropMasks = 'DATA/TRAIN_VAL/all_cropped_masks/masks/'

LoadImagesForAug =  './DATA/TRAIN_VAL/all_cropped_images/images/'
LoadMasksForAug = './DATA/TRAIN_VAL/all_weighted_masks/masks/'
SaveAugImages =  './DATA/TRAIN_VAL/all_cropped_images/images/'
SaveAugMasks = './DATA/TRAIN_VAL/all_weighted_masks/masks/'

LoadMasksForWeight = './DATA/TRAIN_VAL/all_cropped_masks/masks/'
SaveWeightMasks = './DATA/TRAIN_VAL/all_weighted_masks/masks/'