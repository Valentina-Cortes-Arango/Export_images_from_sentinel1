"""
Utility functions for SAR image retrieval, validation, and export.

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

This module provides functions to:
1. Get SAR images (first, mean, and median) for a given location and time range.
2. Validate SAR image collections to ensure they meet quality criteria.
3. Generate random coordinates and retrieve SAR images for them.
4. Monitor and export SAR images to Google Drive.

Functions:
- get_sar_first_mean_median_collection(): Get SAR images for a specific location.
- validate_image(): Checks if an image collection meets the requirements.
- get_random_collections(): Generates random coordinates and retrieves SAR data.
- monitoring_task(): Monitors the status of an Earth Engine export task.
- export_image(): Exports SAR images to Google Drive.

Requirements:
- Google Earth Engine authentication.
- The main script should call these functions as needed.
"""

import ee 
import time
import random


def get_sar_first_mean_median_collection(ee, start, end, latitude: float, longitude: float, polarization: str = 'VV', direction: str = 'DESCENDING', dim: int = 512):
    """
    Retrieves the first, mean, and median SAR image collections for a specified location and time range.

    Parameters:
        start (str): Start date in 'YYYY-MM-DD' format.
        end (str): End date in 'YYYY-MM-DD' format.
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        polarization (str): Polarization mode ('VV' or 'VH'). Default is 'VV'.
        direction (str): Orbit pass direction ('ASCENDING' or 'DESCENDING'). Default is 'DESCENDING'.
        dim (int): Minimum required image dimension (in pixels). Default is 512.


    Returns:
        tuple: First SAR image, mean SAR image, median SAR image, and the SAR collection.
        If the collection is not valid, returns (None, None, None, None).
    """
    degrees = 0.5
    points = [
        ee.Geometry.Point(longitude - degrees / 2, latitude - degrees / 2),
        ee.Geometry.Point(longitude - degrees / 2, latitude + degrees / 2),
        ee.Geometry.Point(longitude + degrees / 2, latitude - degrees / 2),
        ee.Geometry.Point(longitude + degrees / 2, latitude + degrees / 2)
    ]

    dimensions = 1
    roi_expansion_factor = 0

    try:
        while dimensions < dim:
            roi = ee.Geometry.Point([longitude, latitude]).buffer(distance=(dim + roi_expansion_factor) * 10 / 2).bounds()
            sentinel_1_collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                .filter(ee.Filter.listContains('transmitterReceiverPolarisation', polarization))
                .filterBounds(points[0])
                .filterBounds(points[1])
                .filterBounds(points[2])
                .filterBounds(points[3])
                .filterDate(start, end)
                .filter(ee.Filter.eq('instrumentMode', 'IW'))
                .filter(ee.Filter.eq('orbitProperties_pass', direction))
                .select(polarization))

            dimensions = sentinel_1_collection.first().clip(roi).getInfo()['bands'][0]['dimensions'][0]
            roi_expansion_factor += 1

        return sentinel_1_collection.first().clip(roi), sentinel_1_collection.mean().clip(roi), sentinel_1_collection.median().clip(roi), sentinel_1_collection
    except Exception:
        return None, None, None, None


def validate_image(first_vh, collection_vv, collection_vh, average_vh):
    """
    Validates SAR image collections based on size and mean VH value.

    Parameters:
        first_vh: First VH image used for validation.
        collection_vv: SAR VV image collection.
        collection_vh: SAR VH image collection.
        average_vh: Mean VH image used to check water presence.

    Returns:
        bool: True if the collection is valid, False otherwise.
    """
    if collection_vv is None or collection_vh is None:
        print("There are no collections")
        return False

    collection_vv_size = collection_vv.size().getInfo()
    if collection_vv_size < 9 or collection_vv_size > 12:
        print("There are not enough images in the collection")
        return False

    vh_mean_value = average_vh.reduceRegion(reducer=ee.Reducer.mean(), geometry=first_vh.geometry(), scale=10).get('VH').getInfo()
    if vh_mean_value < -20.0:
        print("The collection is in the water")
        return False

    return True


def get_random_collections():
    """
    Generates random coordinates and retrieves SAR image collections.

    Returns:
        dict: A dictionary containing first, mean, and median images for VV and VH polarizations.
    """
    latitude = random.uniform(-89, 89)
    longitude = random.uniform(-179, 179)
    day = random.randint(1, 28)
    month = random.randint(1, 6)
    year = random.randint(17, 23)
    start_date = f'20{year}-{month}-{day}'
    end_date = f'20{year}-{month + 6}-{day}'

    first_vv, mean_vv, median_vv, collection_vv = get_sar_first_mean_median_collection(start_date, end_date, latitude, longitude, polarization='VV')
    first_vh, mean_vh, median_vh, collection_vh = get_sar_first_mean_median_collection(start_date, end_date, latitude, longitude, polarization='VH')

    return {
        "first_vv": first_vv,
        "mean_vv": mean_vv,
        "median_vv": median_vv,
        "collection_vv": collection_vv,
        "first_vh": first_vh,
        "mean_vh": mean_vh,
        "median_vh": median_vh,
        "collection_vh": collection_vh,
    }


def monitoring_task(task):
    """
    Monitors the status of an Earth Engine export task.

    Parameters:
        task: The Earth Engine task to be monitored.
    """
    while task.active():
        status = task.status()
        state = status.get('state')
        if state in ["FAILED", "CANCELLED"]:
            print(f"Task failed: {status.get('error_message')}")
            break
        time.sleep(1)


def export_image(image, folder, file_name):
    """
    Exports an image to Google Drive.

    Parameters:
        image: The image to export.
        folder (str): The Google Drive folder where the image will be saved.
        file_name (str): The name of the exported file.

    Returns:
        dict: The status of the export task.
    """
    task = ee.batch.Export.image.toDrive(
        image=image,
        folder=folder,
        fileNamePrefix=file_name,
        scale=10
    )
    task.start()
    monitoring_task(task)
    return task.status()
