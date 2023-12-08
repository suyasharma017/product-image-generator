from pymongo import MongoClient
from bson import json_util
import json
import datetime
from uuid import uuid4
import boto3
import io
import time
import json
import os
import concurrent.futures
from time import sleep
from pyppeteer import launch
import asyncio
import json
from urllib.parse import urlparse
# Define constant
dev_mode = False

# === Defalut Data ===
CAM_ID = {
    "bridal_set_BS0037":1,
    "solitaire_engagement_ring_SR014": 1,  # 1
    "side_stone_engagement_rings_SSR015": 1,  # 1
    "halo_rings_engagement_HR016": 1,  # 1
    "hidden_halo_engagement_rings_HHR017": 1,  # 1
    "three_stone_engagement_rings_TSR018": 2,  # 2
    "fashion_ring_FR027": 2,  # 2
    "half_eternity_bands_HEB019": 2, #2
    "wedding_band_WD10":2, #2
    "ring_enhancers_RE11":2, #2
    "full_eternity_bands_FEB020": 2, #2
    "fashion_band_FB028": 2, #2
    "men_s_bands_MSB021": 2, #2
    "eternity_bands_EB37": 2, #2
    "anniversary_band_AB38": 2, #2
    "men_s_fashion_band_025": 2, #2
    "stackable_rings_SR029": 2, #2
    "studs_S030": 3, #3
    "men_s_studs_MSS023": 3, #3
    "men_s_earring_MSE023": 3, #3
    "men_s_ring_MSR022": 1, #1
    "men_s_bracelet_MSB_011": 7, #7
    "men_s_necklace_MSN_011": 5, #5
    "hoops_H031":  4, #4
    "tennis_necklace_TN033": 5,  # 5
    "riviera_necklace_RN034": 5,  # 5
    "solitaire_pendant_SP035": 6,  # 6
    "fashion_necklace_FN036": 5,  # 5
    "fashion_pendant_FP036":  10,  # 10
    "men_s_pendant_MSP026": 10,  # 10
    "tennis_bracelet_TB022": 7, #7
    "fashion_bracelet_FB12": 7, #7
    "bangles_BB12": 7, #7
    "anklet_AA10": 7, #7
    "men_s_bracelet_MSB024":  7, #7
    "fashion_earrings_FE032":  8, #8
    "earring_jackets_EJ012": 8, #8
    "123SO": 2
}

pem_path = "./global-bundle.pem"

connection_string = (
    "INSERT_Connection_Strin"
)

# Define a list to store information about failed images
failed_images = []

db_client = MongoClient(connection_string)

db = db_client["von_prod_db"]
collection_names = db.list_collection_names()
print("collection_names >>>>", collection_names)
# === Boto3 Setup ===

s3_client = boto3.client(
    "s3",
    aws_access_key_id="AWS_KEY",
    aws_secret_access_key="Secret_KEY",
    region_name="us-east-1"
)

s3 = boto3.client('s3', aws_access_key_id="AWS_KEY", aws_secret_access_key="Secret_KEY")



ec2_client = boto3.client(
    "ec2",
    aws_access_key_id="AWS_KEY",
    aws_secret_access_key="Secret_KEY",
    region_name="us-east-1",
)

# === Common Funcitons ===
def get_metal_key(metal_name):
    metal_key = "whiteGold"
    for key in ["roseGold", "yellowGold", "whiteGold"]:
        if key.lower() in str(metal_name).lower().replace(" ", ""):
            metal_key = key
            break
    return metal_key

def getProductData(product_id):
    product_data = db.products.aggregate(
        [
            {"$match": {"product_id": product_id}},
            {
                "$lookup": {
                    "from": "parent_products",
                    "localField": "parent_id",
                    "foreignField": "parent_id",
                    "as": "parent_details",
                }
            },
        ]
    )
    product_data = json.loads(json_util.dumps(product_data))
    return product_data

def extract_s3_key_from_url(s3_url):
    # Parse the URL
    parsed_url = urlparse(s3_url)
    # Extract the path, which is the S3 object key
    s3_key = parsed_url.path.lstrip('/')
    s3_key = s3_key.replace("+", " ")
    print('key: ', s3_key)
    return s3_key

async def run_puppeteer(data, page):
    try:
        file_key = data["file_key"]
        product_id = data["product_id"]

        product_data = getProductData(data["product_id"])
        # Check if product is there
        if len(product_data) > 0:
            product_data = product_data[0]
        else:
            print('PARENT DETAILS NOT FOUND')
            return
        key = extract_s3_key_from_url(file_key)
        try:
            s3.put_object_acl(
                Bucket="vondiamonds-rendering-models",
                Key=key,
                ACL='public-read'
            )
        except Exception as e:
            print('Falied to make s3 link public :', e)
        
        
        parent_data = {}
        if 'parent_details' in product_data and len(product_data["parent_details"]) > 0:
            parent_data = product_data["parent_details"][0]
        else:
            print('PARENT DETAILS NOT FOUND-2')
            return
        
        sub_sub_category_key = parent_data["style"]
        cam_angle_id_value = CAM_ID[sub_sub_category_key]
        
        url_to_capture = f"https://d3qli2ony7uccx.cloudfront.net/index.html?fileUrl={file_key}&metalColor={get_metal_key(product_data['metal_type'])}&camId={cam_angle_id_value}&mode=capture&camAngle=imageViewOne&productName=scene_main_{product_id}"
        print("Generating for Product: ",data["product_id"], product_data['metal_type'], url_to_capture)
        # Define the desired download path
        download_path = os.getcwd()+''

        # Set the download behavior to save files in the specified path
        await page._client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_path,
        })

        # Set the viewport dimensions
        await page.setViewport({
            'width': 2000,
            'height': 2000
        })

        # Navigate to the specified URL
        await page.goto(url_to_capture, {'timeout': 120000})
        print("Waiting for Model to load...")
        # Wait for a condition (window.stageLoaded === true) with a timeout of 90 seconds
        await page.waitForFunction('window.stageLoaded === true', {'timeout': 180000})
        # Evaluate the captureScreenshot function in the context of the page
        screenshot_data = []

        await page.evaluate('''async () => {
            return await stage.downloadGlb();
        }''')
        print("Glb downloaded, uploading...")
        time.sleep(3)
        totalData = upload_glb(data , product_data)
        print("Uploaded GLB successfully")

        # Set view 1
        print("View 1")
        javascript_code = f'''
        () => {{
        console.log('Camera view 1: ' +{cam_angle_id_value} )
        stage.changeCameraView('{cam_angle_id_value}', 'imageViewOne');
        }}
        '''
        await page.evaluate(javascript_code)

        time.sleep(10)
        # Capture 1
        bitData = await page.evaluate('''() => {
            return stage.captureScreenshot();
        }''',  {'timeout': 20000})
        screenshot_data.append(bitData)
        print("Captured screenshot 1")
        print("View 2")


        javascript_code = f'''
        () => {{
        console.log('Camera view 2: ' +{cam_angle_id_value} )
        stage.changeCameraView('{cam_angle_id_value}', 'imageViewTwo');
        }}
        '''
        await page.evaluate(javascript_code)

        time.sleep(15)

        bitData = await page.evaluate('''() => {
            return window.captureScreenshot();
        }''',  {'timeout': 20000})
        screenshot_data.append(bitData)
        print("Captured screenshot 2")

        time.sleep(3)
        # Return the screenshot data
        return [screenshot_data, totalData]
    except Exception as e:
        print('Error Run Puppeteer:', str(e))
        failed_images.append(data)
        return None

def upload_screenshot(bitArray, file_data, product_data, input):
    try:
        product_id = input["product_id"]
        return_message = {}
        # Check if product parent exist
        parent_data = {}
        if 'parent_details' in product_data and len(product_data["parent_details"]) > 0:
            parent_data = product_data["parent_details"][0]
        else:
            return
        imageTypes = ["main_image", "hoverover_image"]
        # Get screenshot for 2 angles and upload to S3
        for i in range(len(imageTypes)):
            start_time_img = datetime.datetime.now()  
            image_type = imageTypes[i]  

            file_name = f"{parent_data['parent_sku'] if 'parent_sku' in parent_data else ''}-{product_data['product_sku'] if 'product_sku' in product_data else ''}-{image_type}-{str(uuid4().hex)}.png"
            byte_array = bytearray(bitArray[i])
            print("Uploading image ", i)
    
            s3_client.upload_fileobj(
                io.BytesIO(byte_array),
                "von-diamonds",
                f"von-diamonds-prod-product-images/{file_name}",
                ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
            )
            return_data = {
                "file_name": file_name,
                "file_url": "{}{}".format( "https://von-diamonds.s3.amazonaws.com/von-diamonds-prod-product-images/", file_name),
                "timestamp": str(int(round(time.time() * 1000))),
                "datetime": str(datetime.datetime.now()),
                "product_id": product_id,
                "file_type": image_type,
                "key": file_name,
            }
            print("Image Data "+image_type+" :", return_data)
            # return True
            db.files_history.insert_one(return_data)
            db.products.update_one({"product_id": product_id}, {"$set": {image_type: return_data}})

            return_message[image_type] = {"status": 200, "error": ""}
            print(f"time taken for {image_type}", datetime.datetime.now() - start_time_img)

        # Update db and mark is_image_generated as true
        db.products.update_one(
            {"product_id": product_id}, {"$set": {"creator_model": file_data, "is_image_generated": True,'has_image_failed': False}}
        )
    except Exception as e:
        print(f'Error in upload_screenshot for product_id {input["product_id"]}: {str(e)}')
        # Record the failed image in the list
        failed_images.append(input)

def upload_glb(input, product_data = False):
    try:
        product_id = input["product_id"]
        # print(product_id)
        start_time = datetime.datetime.now()
        # Get product with parent data from db
        if(product_data):
            product_data = getProductData(product_id)
        # return True
        # Check if product is there
        if len(product_data) > 0:
            product_data = product_data[0]
        else:
            return

        # Check if product parent exist
        parent_data = {}
        if 'parent_details' in product_data and len(product_data["parent_details"]) > 0:
            parent_data = product_data["parent_details"][0]
        else:
            return
        # print("parent_data >>>>>", parent_data)
        # return True
        
        # Uplaod GLB file
        scene_name = f"{parent_data['parent_sku'] if 'parent_sku' in parent_data else ''}-{product_data['product_sku'] if 'product_sku' in product_data else ''}-{str(uuid4())}.glb"
        # try:
        s3_client.upload_file(
            f"./scene_main_{product_id}.glb",
            "von-diamonds",
            f"von-diamonds-prod-wm-product-files-glb/{scene_name}",
            ExtraArgs={"ACL": "public-read"},
        )
        # except Exception as e:
        #     print("An error occurred during upload:", e)
        file_data = {
            "file_name": scene_name,
            "file_url": "{}{}".format(
                "https://von-diamonds.s3.amazonaws.com/von-diamonds-prod-wm-product-files-glb/", scene_name
            ),
            "timestamp": str(int(round(time.time() * 1000))),
            "datetime": str(datetime.datetime.now()),
            "product_id": product_id,
            "file_type": "creator_model",
            "key": scene_name,
        }
        # return True
        print("GLB DATA: ", file_data)

        if os.path.exists(f"./scene_main_{product_id}.glb"):
            os.remove(f"./scene_main_{product_id}.glb")
        file = {
            'fileData': file_data,
            'productData': product_data,
            'id': product_id,
        }
        # data.append(file)
        # upload_screenshot(False,file_data, product_data, input)

        print(f"overall time taken", datetime.datetime.now() - start_time)
        return file
    except Exception as e:
        print(f'Error in upload_glb for product_id {input["product_id"]}: {str(e)}')
        # Record the failed image in the list
        failed_images.append(input)

async def process_image(image):
    try:
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        browser = None
        # executablePath='/usr/bin/google-chrome-stable', headless=False
        browser = await launch(executablePath='/usr/bin/google-chrome-stable',options={'args': ['--no-sandbox']})  # Create a new browser instance
        page = await browser.newPage()  # Create a new page in the browser
        print("Browser started...")
        # Your existing code for processing the image goes here...
        data = await run_puppeteer(image, page)  # Pass the page to run_puppeteer
        screenshot_data = data[0]
        if screenshot_data is not None and len(screenshot_data) > 0:
            upload_screenshot(screenshot_data, data[1]['fileData'], data[1]['productData'], image)
        else:
            print(f"Failed to process image: {image['product_id']}")
            # Record the failed image in the `failed_images` list
            failed_images.append(image)
        await browser.close()  # Close the browser instance when done
    except Exception as e:
        print(f"Error processing image {image['product_id']}: {str(e)}")
        if browser:
            await browser.close()  # Close the browser instance when done
        # Record the failed image in the `failed_images` list
        failed_images.append(image)




# === Main Funciton ===
# def mainFunc():
if __name__ == '__main__':
    try:
        # Update db on instance start
        if dev_mode == False:
            print("dev_mode False if cond")
            db.ec2_data.insert_one(
                {
                    "message": f"EC2 Started at {str(int(round(time.time() * 1000)))}",
                    "timestamp": str(int(round(time.time() * 1000))),
                }
            )
            db.store_data.update_one({"id": "id"}, {"$set": {"generate1": True}})#generate1 generate2

        # db.products.update_many({"parent_sku": {"$in": ["TB0010"]}}, {"$set": {"is_image_generated": True}})
        products_list = db.products.find(
                {
                "$and": [
    
                    {"selected_image": True},
                    {"render_model_file_link": {"$exists": True}},
                ]
            }
        )
        products_list = json.loads(json_util.dumps(products_list))
        print("length  of prdt >>>>>>>>", len(products_list))
        # return True
        image_genrate_list = []  # List of images to process

        for product in products_list:
            if "render_model_file_link" in product:
                image_genrate_list.append(
                    {
                        "product_id": product["product_id"],
                        "parent_id": product["parent_id"],
                        "key": product["render_model_file_link"]["key"],
                        "file_key": product["render_model_file_link"]["file_url"],
                    }
                )

        
        print("image_genrate_list >>>>>>>>>>", image_genrate_list)
        t1 = datetime.datetime.now()
        # threads = min(49, len(image_genrate_list) if len(image_genrate_list) != 0 else 49)
        # with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        #     executor.map(generate_image, image_genrate_list)
        print(f"Time take to process {len(image_genrate_list)} =>", datetime.datetime.now() - t1)


        # Create a new event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Process images using a thread pool for parallel execution
        # image_genrate_list = image_genrate_list[:3]
        # threads = min(3, len(image_genrate_list) if len(image_genrate_list) != 0 else 3)
        # print('Max Threads: ', threads)
        # with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        #     # Use loop.run_until_complete to run the coroutine in the thread
        #     loop.run_until_complete(asyncio.gather(*[process_image(image) for image in image_genrate_list]))
        
        for image in image_genrate_list:
            asyncio.run(process_image(image))
        # Retry failed images twice
        max_retries = 2
        for retry_count in range(max_retries):
            print(f"Retrying failed images (Attempt {retry_count + 1}/{max_retries})")
            failed_images_copy = failed_images.copy()
            failed_images.clear()
            for image in failed_images_copy:
                asyncio.run(process_image(image))

        for image in failed_images:
            # Update db and mark is_image_generated as true
            db.products.update_one(
                {"product_id": image["product_id"]}, {"$set": {'has_image_failed': True}}
            )
            
        sleep(50)
        if failed_images:
            print("Failed images:")
            for failed_image in failed_images:
                print(f"Product ID: {failed_image['product_id']}")
        # Update db and shotdown
        # sleep(50000)
        if dev_mode == False:
            db.store_data.update_one({"id": "id"}, {"$set": {"generate2": False}})
            db.ec2_data.insert_one(
                {
                    "message": f"Ec2 Stopped at {str(int(round(time.time() * 1000)))}",
                    "timestamp": str(int(round(time.time() * 1000))),
                }
            )
            print("end of function >>>>>>>>>>>")
            ec2_client.stop_instances(InstanceIds=["INSTACE_ID"])
    except Exception as e :
        print("exception >>>>>>>>>>>>>>>", e)
        sleep(5)
        if dev_mode == False:
            print("e >>>>>>>", e)
            db.store_data.update_one({"id": "id"}, {"$set": {"generate2": False}})
            db.ec2_data.insert_one(
                {
                    "message": f"Ec2 Stopped and Failed at {str(int(round(time.time() * 1000)))}",
                    "error":e,
                    "timestamp": str(int(round(time.time() * 1000))),
                }
            )
            ec2_client.stop_instances(InstanceIds=["INSTACE_ID"])
# generate_image()