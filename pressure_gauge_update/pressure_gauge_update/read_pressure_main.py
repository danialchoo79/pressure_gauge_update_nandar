# Selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# helpers
import helper
import pressure_reading as pr
import pressure_notification as pn

# Commons
import io
import arrow
import os
import logging
import json
import db_helper as db
from logging.handlers import RotatingFileHandler
import time


def main():

    try:
        print("Staring program")

        # Load adminConfigs
        main_config, db_config = helper.get_config()
        spt_db_connections = db_config["spt_db_connections"]

        # Start Logger
        logger = helper.start_logger(main_config)

        # Retrieve Config
        logger.info("Retreving line config")
        line_config = main_config["line_config"]

        # Init Driver
        static_chromeDriver = main_config["static_chromeDriver"]
        driver = helper.INIT_DRIVER(static_chromeDriver)
        print(driver.get_window_size())
        logger.info("Driver Inited")

        # Creating base folder to store
        output_path = helper.create_base_folder(main_config)
        logger.info("Created Base Folder")

        # Retrieve base information on host
        hostname, fqdn, local_ip = helper.get_host_info()
        program_mode = main_config["program_mode"]
        program_version = main_config["program_version"]
        run_date = arrow.now().format("YYYY-MM-DD")

        for line_key, line_value in line_config.items():
            logger.info("Running Line : ".format(line_key))

            params = (
                line_key,
                run_date,
                hostname,
                fqdn,
                local_ip,
                program_mode,
                program_version,
            )

            run_id = db.create_pressure_header_main(params, spt_db_connections)

            # Generate line key information
            for pump_key, pump_value in line_value.items():
                # Retrieve url
                url_path = pump_value["URL"]
                logger.info("Running pump : ".format(pump_key))
                logger.info("URL : ".format(url_path))

                # INIT
                spec_id = 1
                status = ""
                status_msg = ""
                result = ""
                try:
                    driver.set_page_load_timeout(2)
                    try:
                        logger.info("Attempting to open URL")
                        # driver.get(url_path)
                        html_content = """
                        <!DOCTYPE html>
                        <html style="height: 100%;">
                        <head>
                            <meta name="viewport" content="width=device-width, minimum-scale=0.1">
                        </head>
                        <body style="margin: 0px; background: #0e0e0e; height: 100%">
                            <img style="display: block;-webkit-user-select: none;margin: auto;position: absolute; top: 0;left: 0;background-color: hsl(0, 0%, 25%);" src="http://128.53.209.100/stream">
                        </body>
                        </html>
                        """

                        # Create a temporary HTML file
                        with open("temp.html", "w") as f:
                            f.write(html_content)
                        # Open the HTML file with the driver
                        driver.get(
                            "file://" + "C:/nandar/pressure_gauge_update/temp.html"
                        )
                    except Exception as e:
                        logger.info("Driver time out")

                    logger.info("URL opened and stopped")

                    try:
                        logger.info("Checking for element")
                        img_element = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.TAG_NAME, "img"))
                        )
                        logger.info("Element Exists")
                    except Exception as e:
                        logger.error(e)
                        raise Exception("Unable to retrieve image from url")

                    try:
                        # Save image and write
                        logger.info("Saving Images")
                        image_path_cropped = helper.save_image(
                            driver, line_key, pump_key, output_path, main_config
                        )
                        logger.info("Images Saved")
                    except Exception as e:
                        logger.error(e)
                        raise Exception("Unable to save Image")

                    try:
                        # Run Image processing
                        result = pr.main(
                            image_path_cropped, output_path, line_key, pump_key
                        )
                    except Exception as e:
                        logger.error(e)
                        raise Exception("Unable to generate result from image")

                    try:
                        # Run Notifications
                        print("--------------------")
                        print(result)
                        threshold = pump_value["THRESHOLD"]
                        if float(result) > threshold:
                            # pn.trigger_pressure_notify(line_key, pump_key, result)
                            print("Alert")
                    except Exception as e:
                        logger.error(e)
                        raise Exception("Unable to send message to workplace")

                    # INSERT INTO DB
                    try:
                        spec_id = 1
                        status = "PASS"
                        status_msg = "PASS"
                        run_data_param = (
                            run_id,
                            spec_id,
                            status,
                            status_msg,
                            result,
                            output_path,
                        )
                        db.create_run_data_main(run_data_param, spt_db_connections)
                    except Exception as e:
                        raise e

                except Exception as e:
                    print(e)
                    logger.error(e)
                    status = "FAIL"
                    status_msg = e
                    run_data_param = (
                        run_id,
                        spec_id,
                        status,
                        status_msg,
                        result,
                        output_path,
                    )
                    logger.error(run_data_param)
                    db.create_run_data_main(run_data_param, spt_db_connections)
                    logger.error("Error completed")
                    pass

    except Exception as e:
        pass
    finally:
        if driver is not None:
            driver.close()
            logger.info("Driver Closed")
            driver = None


if __name__ == "__main__":
    # for i in range(0, 100):
    main()
    time.sleep(5)
    # "HOST" : "128.53.1.71"
