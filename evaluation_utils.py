#TODO: check imports and function definitions to exclude the ones that are no longer relevant


import argparse
parser = argparse.ArgumentParser(description='Run evaluation pipeline for specified model name')
parser.add_argument('model_name', metavar='name', type=str,  default="ResUnet", # nargs='+',
	            help='Name(s) of the model(s) to evaluate.')
parser.add_argument('--out_folder', metavar='folder', type=str,  default="results",
	            help='Output folder.')	
args = parser.parse_args()

from pathlib import Path

# setup paths --> NOTE: CURRENT PATHS ARE TO BE UPDATED
repo_path = Path("/home/luca/PycharmProjects/cell_counting_yellow")
TRAIN_IMG_PATH = repo_path / "DATASET/OLD/sample_valid/images"
TRAIN_MASKS_PATH = repo_path / "DATASET/OLD/sample_valid/masks"

# define auxiliary functions --> NOTE: TO CHECK REDUNDANCY WITH OTHER UTILS SCRIPTS

### Model utils
def mean_iou(y_true, y_pred):
    prec = []
    t = 0.95
    y_pred_ = tf.to_int32(y_pred > t)
    score, up_opt = tf.metrics.mean_iou(y_true, y_pred_, 2)
    K.get_session().run(tf.local_variables_initializer())
    with tf.control_dependencies([up_opt]):
        score = tf.identity(score)
    prec.append(score)
    return K.mean(K.stack(prec), axis=0)

smooth = 1.

def dice_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def create_weighted_binary_crossentropy(zero_weight, one_weight):

    def weighted_binary_crossentropy(y_true, y_pred):

        b_ce = K.binary_crossentropy(y_true, y_pred)

        # Apply the weights
        weight_vector = y_true * one_weight + (1. - y_true) * zero_weight
        weighted_b_ce = weight_vector * b_ce

        # Return the mean error
        return K.mean(weighted_b_ce)

    return weighted_binary_crossentropy
    
### Post-processing utils
def mask_post_processing(thresh_image, area_threshold=600, min_obj_size=200, max_dist=30):

    # Find object in predicted image
    labels_pred, nlabels_pred = ndimage.label(thresh_image)
    processed = remove_small_holes(labels_pred, area_threshold=area_threshold, connectivity=8,
                                   in_place=False)
    processed = remove_small_objects(
        processed, min_size=min_obj_size, connectivity=1, in_place=False)
    labels_bool = processed.astype(bool)

    distance = ndimage.distance_transform_edt(processed)

    maxi = ndimage.maximum_filter(distance, size=max_dist, mode='constant')
    local_maxi = peak_local_max(maxi, indices=False, footprint=np.ones((40, 40)),
                                exclude_border=False,
                                labels=labels_bool)

    local_maxi = remove_small_objects(
        local_maxi, min_size=25, connectivity=1, in_place=False)
    markers = ndimage.label(local_maxi)[0]
    labels = watershed(-distance, markers, mask=labels_bool,
                       compactness=1, watershed_line=True)

    return(labels.astype("uint8")*255)

### Evaluation utils
def make_UNet_prediction(img_path, threshold, model, colorspace="rgb"):

    # read input image
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = np.expand_dims(img, 0)

    # compute prediction
    predicted_map = model.predict(img/255.)

    # threshold the predicted heatmap
    thresh_image = np.squeeze((predicted_map > threshold).astype('uint8'))
    thresh_image = mask_post_processing(thresh_image)

    return(thresh_image)


def compute_metrics(pred_mask_binary, mask, metrics, img_name):
    # extract predicted objects and counts
    pred_label, pred_count = ndimage.label(pred_mask_binary)
    pred_objs = ndimage.find_objects(pred_label)

    # compute centers of predicted objects
    pred_centers = []
    for ob in pred_objs:
        pred_centers.append(((int((ob[0].stop - ob[0].start)/2)+ob[0].start),
                             (int((ob[1].stop - ob[1].start)/2)+ob[1].start)))

    # extract target objects and counts
    targ_label, targ_count = ndimage.label(mask)
    targ_objs = ndimage.find_objects(targ_label)

    # compute centers of target objects
    targ_center = []
    for ob in targ_objs:
        targ_center.append(((int((ob[0].stop - ob[0].start)/2)+ob[0].start),
                            (int((ob[1].stop - ob[1].start)/2)+ob[1].start)))

    # associate matching objects, true positives
    tp = 0
    fp = 0
    for pred_idx, pred_obj in enumerate(pred_objs):

        min_dist = 50  # 1.5-cells distance is the maximum accepted
        TP_flag = 0

        for targ_idx, targ_obj in enumerate(targ_objs):

            dist = hypot(pred_centers[pred_idx][0]-targ_center[targ_idx][0],
                         pred_centers[pred_idx][1]-targ_center[targ_idx][1])

            if dist < min_dist:

                TP_flag = 1
                min_dist = dist
                index = targ_idx

        if TP_flag == 1:
            tp += 1
            TP_flag = 0

            targ_center.pop(index)
            targ_objs.pop(index)

    # derive false negatives and false positives
    fn = targ_count - tp
    fp = pred_count - tp

    # update metrics dataframe
    metrics.loc[img_name] = [tp, fp, fn, targ_count, pred_count]

    return(metrics)


def F1Score(metrics):
    # compute performance measure for the current quantile filter
    tot_tp_test = metrics["TP"].sum()
    tot_fp_test = metrics["FP"].sum()
    tot_fn_test = metrics["FN"].sum()
    tot_abs_diff = abs(metrics["Target_count"] - metrics["Predicted_count"])
    tot_perc_diff = (metrics["Predicted_count"] -
                     metrics["Target_count"])/(metrics["Target_count"]+10**(-6))
    accuracy = (tot_tp_test + 0.001)/(tot_tp_test +
                                      tot_fp_test + tot_fn_test + 0.001)
    precision = (tot_tp_test + 0.001)/(tot_tp_test + tot_fp_test + 0.001)
    recall = (tot_tp_test + 0.001)/(tot_tp_test + tot_fn_test + 0.001)
    F1_score = 2*precision*recall/(precision + recall)
    MAE = tot_abs_diff.mean()
    MedAE = tot_abs_diff.median()
    MPE = tot_perc_diff.mean()

    return(F1_score, MAE, MedAE, MPE, accuracy, precision, recall)  
    
### Plotting utils
def plot_thresh_opt(df, save_path=None):
    line = df.plot(y="F1", linewidth=2, markersize=6, legend=False), 
    line = plt.title('$F_1$ score: threshold optimization', size =18, weight='bold')
    line = plt.ylabel('$F_1$ score', size=15)
    line = plt.xlabel('Threshold', size=15 )
    line = plt.axvline(df.F1.idxmax(), color='firebrick', linestyle='--')
    if save_path:
        outname = save_path / 'f1_score_thresh_opt_{}.png'.format(model_name[:-3])
        _ = plt.savefig(outname, dpi = 900, bbox_inches='tight' )
    return line  
    
if __name__ == "__main__":

	from skimage.feature import peak_local_max
	from skimage.morphology import remove_small_holes, remove_small_objects, label
	from skimage.segmentation import watershed
	from skimage.filters import sobel
	from scipy import ndimage
	from math import hypot
	import pandas as pd
	import numpy as np

	from tqdm import tqdm
	import cv2
	from matplotlib import pyplot as plt

	from keras.models import load_model, Model, Sequential
	from keras import backend as K
	import tensorflow as tf

	model_name = "{}.h5".format(args.model_name)
	model_path = "{}/model_results/{}".format(repo_path, model_name)
	save_path = repo_path / args.out_folder
	save_path.mkdir(parents=True, exist_ok=True)
#	print(model_path, save_path)
	WeightedLoss = create_weighted_binary_crossentropy(1, 1.5)
	model = load_model(model_path, custom_objects={'mean_iou': mean_iou, 'dice_coef': dice_coef, 
			                                    'weighted_binary_crossentropy': WeightedLoss}, compile=False)      
	threshold_seq = np.arange(start=0.2, stop=0.9, step=0.05)
	metrics_df_validation_rgb = pd.DataFrame(None, columns=["F1", "MAE", "MedAE", "MPE", "accuracy",
			                                        "precision", "recall"])

	for _, threshold in tqdm(enumerate(threshold_seq), total=len(threshold_seq)):
		# create dataframes for storing performance measures
		validation_metrics_rgb = pd.DataFrame(
		columns=["TP", "FP", "FN", "Target_count", "Predicted_count"])
		# loop on training images
		for _, img_path in enumerate(TRAIN_IMG_PATH.iterdir()):
			mask_path = TRAIN_MASKS_PATH / img_path.name

			# compute predicted mask and read original mask
			img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)

			pred_mask_rgb = make_UNet_prediction(
			    img_path, threshold, model)
			mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
			compute_metrics(pred_mask_rgb, mask,
					validation_metrics_rgb, img_path.name)
		metrics_df_validation_rgb.loc[threshold] = F1Score(validation_metrics_rgb)
	outname = save_path / 'metrics_{}.csv'.format(model_name[:-3])
	metrics_df_validation_rgb.to_csv(outname, index = True, index_label='Threshold')
	_ = plot_thresh_opt(metrics_df_validation_rgb, save_path)
