# %% Initialization
import sys
from pathlib import Path

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from joblib import dump, load

basefolder_loc = Path(__file__).parents[1]
sys.path.append(str(basefolder_loc))
from utils.load_image import get_all_images


# %% load data
def load_data(dataframe):
    image_generator = get_all_images(dataframe)

    all_images = []
    all_targets = []
    all_cell_codes = []
    for data in image_generator:
        # Crop image to center reduce the image to 25%
        original = data[0]
        width, height = original.size  # Get dimensions
        left = width / 4
        top = height / 4
        right = 3 * width / 4
        bottom = 3 * height / 4
        cropped_example = original.crop((left, top, right, bottom))

        # Drop the empty red channel reducing the image to 16.7%
        img_np = np.array(cropped_example)[:, :, 1:]

        # Add everything to lists
        all_images.append(img_np.flatten())
        all_targets.append(data[2])
        all_cell_codes.append(data[1])

    return np.array(all_images, dtype=np.uint8), all_targets, all_cell_codes


# %% transforms data
def transform_images(all_images, all_targets, all_cell_codes, location):
    images_pca = pca.transform(all_images)

    test_df = pd.DataFrame(
        pd.np.column_stack([all_cell_codes, all_targets, images_pca]),
        columns=["cell_codes", "targets"]
        + [
            f"eigen_value_{str(i).zfill(4)}"
            for i in range(images_pca.shape[1])
        ],
    )
    test_df.to_csv(location, sep="\t", float_format="%.6f", index=False)


# %% Check if what files need to be created
num_eigen_values = 2000

model_loc = os.path.join(Path(__file__).parents[0], "models")
os.makedirs(model_loc, exist_ok=True)

figures_loc = os.path.join(Path(__file__).parents[0], "figures")
os.makedirs(figures_loc, exist_ok=True)

model_name = os.path.join(model_loc, "PCA_model.joblib")
loc_training_eigenvalues = os.path.join(
    Path(__file__).parents[0], "data", "train_eigen_values.tsv.gz"
)
loc_test_eigenvalues = os.path.join(
    Path(__file__).parents[0], "data", "test_eigen_values.tsv.gz"
)
does_model_exists = os.path.isfile(model_name)
does_training_eigen_exists = os.path.isfile(loc_training_eigenvalues)
does_test_eigen_exists = os.path.isfile(loc_test_eigenvalues)

# %% load training data
if not does_model_exists or not does_training_eigen_exists:
    print("Start loading all images that match a row in train.tsv.gz")
    dataframe = pd.read_csv(
        os.path.join(Path(__file__).parents[0], "data", "train.tsv.gz"),
        sep="\t",
    )
    (
        all_training_images,
        all_training_targets,
        all_training_cell_codes,
    ) = load_data(dataframe)

# %% Get PCA model
if does_model_exists:
    print("loaded model")
    pca = load(model_name)
else:
    print("model is not found. Training the model on training data")
    pca = PCA(n_components=num_eigen_values)
    pca.fit(all_training_images)
    dump(pca, model_name)

# %% transform training data
if not does_training_eigen_exists:
    print("Start transforming training data")
    transform_images(
        all_training_images,
        all_training_targets,
        all_training_cell_codes,
        loc_training_eigenvalues,
    )

# %% Validation data
if not does_test_eigen_exists:
    print("Start loading all images that match a row in test.tsv.gz")
    dataframe = pd.read_csv(
        os.path.join(Path(__file__).parents[0], "data", "test.tsv.gz"),
        sep="\t",
    )

    (
        all_validation_images,
        all_validation_targets,
        all_validation_cell_codes,
    ) = load_data(dataframe)

    print("Start transforming test data")

    transform_images(
        all_validation_images,
        all_validation_targets,
        all_validation_cell_codes,
        loc_test_eigenvalues,
    )
# %% show information lost
plt.figure(1, figsize=(12, 8))

plt.plot(pca.explained_variance_ratio_, linewidth=2)

print(f"Total information {np.sum(pca.explained_variance_ratio_):.4}")
plt.xlabel("Components")
plt.ylabel("Explained Variaces")
plt.savefig(
    os.path.join(
        figures_loc,
        f"information_graph_{np.sum(pca.explained_variance_ratio_):.4}.png",
    )
)
plt.close()
