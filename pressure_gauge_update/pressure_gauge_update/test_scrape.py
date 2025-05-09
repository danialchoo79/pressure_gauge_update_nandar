from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
import urllib.request
import arrow
import cv2
import os
import numpy as np
from skimage import io
import test_ocr_engine as ocr_engine
from pprint import pprint
import test_db as db
import sys
import time


def INIT_DRIVER(static_chromeDriver):
    options = Options()
    #ua = UserAgent(cache=False,fallback='Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko')
    # Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko
    userAgent = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; Trident/7.0; .NET4.0E; .NET4.0C)'
    options.add_argument(f'user-agent={userAgent}')


    #driver = webdriver.PhantomJS(r"C:\Users\J112I8272\Desktop\selenium_driver\phantomjs-2.1.1-windows\bin\phantomjs.exe")
    #driver = webdriver.Ie(r'D:\JERROLD\SELENIUM\AUTOMATIOn_WEB DRIVER\selenium_driver2\IEDriverServer.exe')
    driver = webdriver.Chrome(options=options,executable_path=static_chromeDriver)
    return driver

def main():
    try:

        # STATIC VIABLES
        static_chromeDriver = r'C:\chromedriver\chromedriver.exe'
        main_dict = {
                    "static_server_1" :{
                                            "url_path" : "http://128.53.66.27:8000/status_viewer_dsm.html",
                                            "output_path" : "F:/FLASK_STORAGE/MACHINE_STATUS_OUTPUT/SERVER_1/"
                                        },
                    "static_server_2" :{
                                            "url_path" : "http://128.53.66.29:8000/status_viewer_dsm.html",
                                            "output_path" : "F:/FLASK_STORAGE/MACHINE_STATUS_OUTPUT/SERVER_2/"
                                        }
                    }

        # main_dict = {
        #             "static_server_1" :{
        #                                     "url_path" : "http://128.53.66.27:8000/status_viewer_dsm.html",
        #                                     "output_path" : "C:/Users/administrator.SHDSFA/Desktop/Initial_tests/Output/server_1/"
        #                                 }
        #             }

        # TS
        now = arrow.now()
        date = now.format('YYYY_MM_DD')
        timeStr = now.format('HH_mm_ss')


        upload_date = now.format('YYYY/MM/DD HH:mm:ss')

        driver = None
        for key, value in main_dict.items():
            driver = None
            try:
                # INIT DRIVER
                driver = INIT_DRIVER(static_chromeDriver)

                print(value)
                url_path = value['url_path']
                base_output_path = value['output_path']

                print(url_path)
                # OPEN SITE
                driver.get(url_path)

                # GET IMAGE PATH BY XPATH

                img = driver.find_element_by_xpath("//img[@alt='viewer']")
                src = img.get_attribute('src')

                #FORMULATE OUTPUT PATH
                final_output_path = base_output_path + date + '/' + timeStr

                if not os.path.exists(final_output_path):
                    os.makedirs(final_output_path)

                image = io.imread(src)

                # IMAGE ARRAY
                cv_img = image.astype(np.uint8)

                # LIVE RUN
                print(key)
                run_config = int(key[-1])

                ocr_result = ocr_engine.OCR(run_config, image_array = cv_img)

                # STATIC RUN
                #ocr_result = ocr_engine.OCR(1, imagePath =r"C:\Users\j112i8272\Desktop\Python\MU_SCRAPPING\output\server_1\2020_04_03\11_28_54\image.png")

                pprint(ocr_result)

                # GENERATE RUN LINE DATA BASED IB OCR RESULTS
                print("attempting to insert data")
                db.upload_data_main(ocr_result,upload_date)
                # PROCESS DATA
                urllib.request.urlretrieve(src, final_output_path+'/image.png')

                time.sleep(2)
                if driver is not None:
                    driver.close()
                    driver = None

            except Exception as e:

                if driver is not None:
                    driver.close()
                    driver = None

                raise e
            finally:
                if driver is not None:
                    driver.close()
                    driver = None


    except Exception as e:
        print(e)
    finally:
        if driver is not None:
            driver.close()
            driver = None

if __name__ == '__main__':
    main()
