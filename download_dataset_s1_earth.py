"""
Authors: 
- Valentina Cortes-Arango
- Jean Pierre Díaz-Paz
- Rubén Darío Vásquez-Salazar
- Juan Andrés Jaramillo-Pineda 
- Carlos M. Travieso-Gonzalez
- Luis Gómez
- Ahmed Alejandro Cardona-Mesa


Date: March 2025
License: GPL-3.0

This script retrieves and exports SAR images from Google Earth Engine (GEE) 
using random coordinates and a predefined validation process.

The workflow follows these steps:
1. Authenticate and initialize GEE.
2. Generate random geographic coordinates.
3. Validata SAR images (VV and VH polarizations).
4. Validate the image collection to ensure it meets quality criteria.
5. Export the selected images to Google Drive, avoiding duplicates.

Parameters:
- The number of images to export is set to 2100.
- Exported images include first, mean, and median values for both VV and VH polarizations.
- The export process ensures no repeated images by storing processed IDs in a set.

Requirements:
- Google Earth Engine authentication.
- The `utils` module must provide `get_random_collections()`, `validate_image()`, and `export_image()`.
"""

import ee
import random
from utils import *

random.seed()

# Authenticate and initialize Google Earth Engine
ee.Authenticate()
ee.Initialize(project='your-project-earth-engine')


number_images = 2100
ids = set()
current_image = 0

while current_image < number_images:
    images_dict = get_random_collections()
    if validate_image(images_dict["first_vh"], images_dict["collection_vv"], images_dict["collection_vh"], images_dict["mean_vh"]):
        image_id = images_dict['first_vv'].get('system:index').getInfo()

        if image_id not in ids:
            export_params = [
                ('first_vv', 'SAR VV'),
                ('first_vh', 'SAR VH'),
                ('mean_vv', 'GT MEAN VV'),
                ('mean_vh', 'GT MEAN VH'),
                ('median_vv', 'GT MEDIAN VV'),
                ('median_vh', 'GT MEDIAN VH')
            ]

            for key, folder in export_params:
                export_image(images_dict[key].visualize(**{'min': -25, 'max': 5}), folder, str(current_image + 1))

            ids.add(image_id)
            print(f'Image #{current_image + 1} saved successfully!')
            current_image += 1