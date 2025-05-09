from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# from fake_useragent import UserAgent
from selenium import webdriver
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import arrow
import cv2
import socket

logs = logging.getLogger("PRESSURE")


def INIT_DRIVER(static_chromeDriver):
    try:
        options = Options()
        # ua = UserAgent(cache=False,fallback='Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko')
        # Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko
        userAgent = "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; Trident/7.0; .NET4.0E; .NET4.0C)"
        options.add_argument(f"user-agent={userAgent}")
        options.add_argument(" --disable-browser-side-navigation")
        options.add_argument("window-size=1051,806")
        # options.page_load_strategy = 'eager'
        service = Service(executable_path=static_chromeDriver)
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        raise e


def get_config():
    try:
        main_config_path = open(
            "C:/nandar/pressure_gauge_update/pressure_gauge_update/Config/config.json"
        )
        main_config = json.load(main_config_path)

        db_config_path = open(
            "C:/nandar/pressure_gauge_update/pressure_gauge_update/Sensitive/db_connection.json"
        )
        db_config = json.load(db_config_path)

        return main_config, db_config
    except Exception as e:
        raise e


def start_logger(main_config):
    try:
        log_base_fp = main_config["log_base_fp"]
        logpath = main_config["log_fp"]
        print(log_base_fp)
        if not os.path.exists(log_base_fp):
            os.makedirs(log_base_fp)
            time.sleep(0.5)
        logger = logging.getLogger("PRESSURE")
        if logger.hasHandlers():
            logger.handlers.clear()
        handler = RotatingFileHandler(logpath, maxBytes=2000000, backupCount=30)
        logger.setLevel(logging.DEBUG)
        handler.suffix = "%Y%m%d"
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info("Starting Process")
        logger.info(
            "Get Processing Time \t {}".format(
                arrow.now().format("YYYY-MM-DD_HH-mm-ss")
            )
        )

        return logger
    except Exception as e:
        raise e


def create_base_folder(main_config):
    try:
        dt_obj = arrow.now().format("YYYY_MM_DD_HH_mm_ss")
        base_output_path = main_config["base_output_path"]
        output_path = base_output_path + "/" + dt_obj
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        return output_path
    except Exception as e:
        raise e


def save_image(driver, line_key, pump_key, output_path, main_config):
    try:
        image_filename_ori = "{}_{}_ori.png".format(line_key, pump_key)
        image_filename_adj = "{}_{}_adj.png".format(line_key, pump_key)
        image_filename_cropped = "{}_{}_cropped.png".format(line_key, pump_key)
        image_path_ori = output_path + "/" + image_filename_ori
        image_path_adj = output_path + "/" + image_filename_adj
        image_path_cropped = output_path + "/" + image_filename_cropped
        # Save
        driver.save_screenshot(image_path_ori)
        img_obj = cv2.imread(image_path_ori)
        img_ccw_90 = cv2.rotate(img_obj, cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite(image_path_adj, img_ccw_90)

        #
        img_cropped = cv2.imread(image_path_adj)
        #  X:X Y:Y
        cropImg = img_cropped[31:550, 200:750]

        #  YY
        # cropImg[340:380, 205:315] = (255, 255, 255)
        cropImg[320:380, 205:315] = (255, 255, 255)
        #
        cv2.imwrite(image_path_cropped, cropImg)

        return image_path_cropped
    except Exception as e:
        raise e


def get_host_info():
    """
    [summary]

    Retrieve Computer Information

    Returns:
        hostname -- Computer Name,
        fqdn -- domain
        local_ip -- domain ip
    """
    try:
        logs.info("Retrieving Host Info Started")
        hostname = ""
        fqdn = ""
        local_ip = ""

        hostname = socket.gethostname()
        fqdn = socket.getfqdn()
        local_ip = socket.gethostbyname(fqdn)

        return hostname, fqdn, local_ip
    except Exception as e:
        return hostname, fqdn, local_ip
