# Realistic Product Image Generation
## Overview
This project is designed to generate realistic images of products stored in a database. The process involves fetching product images from an S3 bucket, loading them using Puppeteer, taking screenshots from different angles, uploading the screenshots back to S3, and updating the links in the database.

## Technologies Used
-Python

-MongoDB (pymongo library)

-AWS S3 (boto3 library)

-Puppeteer

-Asyncio

-Concurrent.futures


## Setup
*Install the required Python packages:
bash

pip install pymongo boto3 pyppeteer

*Set up AWS credentials in the code:
python

aws_access_key_id = "YOUR_ACCESS_KEY"
aws_secret_access_key = "YOUR_SECRET_KEY"

*Set the MongoDB connection string:
python

connection_string = "YOUR_MONGODB_CONNECTION_STRING"

Set the appropriate constant values:
dev_mode: Set to True for development mode.
pem_path: Path to the PEM file.
CAM_ID: Dictionary mapping product types to camera IDs.

## Running the Project
Make sure your AWS and MongoDB credentials are correctly set.

Execute the Python script:
bash

python script_name.py

The script will fetch products, generate realistic images, and update the database.

## Notes
-The project uses Puppeteer for headless browser automation to capture realistic product images.

-Images are uploaded to an S3 bucket, and links are updated in the MongoDB database.

-The script includes error handling and retries for failed image processing.

-Feel free to customize the code according to your specific use case and environment.

## Sample Output
![Tennis Necklace](https://github.com/suyasharma017/product-image-generator/assets/107684989/99c7cc65-8001-4856-b1bd-a1329cd88687)

![Three Stone view 2](https://github.com/suyasharma017/product-image-generator/assets/107684989/dce1e6c5-80a6-4c7c-a5ee-248c9f36d7f7)

![Studs ](https://github.com/suyasharma017/product-image-generator/assets/107684989/94301986-a5f1-48d8-a0ae-9dcbd0679d57)

![Wedding Band](https://github.com/suyasharma017/product-image-generator/assets/107684989/3dc92582-8349-45f3-aebf-de31790c9591)

