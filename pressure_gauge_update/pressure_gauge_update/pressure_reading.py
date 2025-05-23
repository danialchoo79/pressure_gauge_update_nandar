"""
Copyright (c) 2017 Intel Corporation.
Licensed under the MIT license. See LICENSE file in the project root for full license information.
"""

from PIL import Image
import cv2
import numpy as np
import time
from PIL import Image
import matplotlib.pyplot as plt
import arrow

def avg_circles(circles, b):

    """ 
        This averages all circles to find the best circle to represent the Gauge 

        It finds the centroid of the best representative circle.   
    """
    
    avg_x = 0
    avg_y = 0
    avg_r = 0
    for i in range(b):
        # optional d- average for multiple circles (can happen when a gauge is at a slight angle)
        # For each circle find the value of x, y, r then compute the average values
        avg_x = avg_x + circles[0][i][0]
        avg_y = avg_y + circles[0][i][1]
        avg_r = avg_r + circles[0][i][2]
    avg_x = int(avg_x / (b))
    avg_y = int(avg_y / (b))
    avg_r = int(avg_r / (b))
    return avg_x, avg_y, avg_r


def dist_2_pts(x1, y1, x2, y2):
    """
        Euclidean Distance is used to calculate straight-line distance in 2D space
    """
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def calibrate_gauge(filepath, output_path, line_key, pump_key):
    """

    Operations:
        (1) Find Circle (center, radius)
        (2) Draw Reference Lines to Read Angles
        (3) Ask User for Gauge Extremes
        (4) Ask for Units
        (5) Return Calibration Info 
                (min_angle, min_value)
                (max_angle, max_value)

    This function should be run using a test image in order to calibrate the range available to the dial as well as the
    units.  It works by first finding the center point and radius of the gauge.  Then it draws lines at hard coded intervals
    (separation) in degrees.  It then prompts the user to enter position in degrees of the lowest possible value of the gauge,
    as well as the starting value (which is probably zero in most cases but it won't assume that).  It will then ask for the
    position in degrees of the largest possible value of the gauge. Finally, it will ask for the units.  This assumes that
    the gauge is linear (as most probably are).
    It will return the min value with angle in degrees (as a tuple), the max value with angle in degrees (as a tuple),
    and the units (as a string)...
    """

    # Reizes Image to (271, 262) using (4x4) Square
    image = cv2.imread(filepath)
    img = cv2.resize(image, dsize=(271, 262), interpolation=cv2.INTER_CUBIC)

    # --TEST CODE--
    # img.save('images\guage-4-271.jpeg')
    # img = cv2.imread(file_type)
    # cv2.imshow('image', img)
    # cv2.waitKey(0); cv2.destroyAllWindows(); cv2.waitKey(1)

    # Get height, width and convert it to gray
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect Circles
    # Restricting the search from 35-48% of Image Height gives the possible radii gives fairly good results across different samples.
    # These are pixel values which correspond to the possible radii search range.30,47 for
    
    circles = cv2.HoughCircles(
        gray,                   # Image
        cv2.HOUGH_GRADIENT,     # Method (Gradient Information of Edges)
        1.5,                    # Accumulator Resolution (accumulates votes based on edge points). Higher = finer resolution, vice versa.                  
        5,                      # Minimum Distance Between Centroids in Pixels
        np.array([]),           # Empty Array (Unused Parameter)
        100,                    # Canny Edge Threshold to detect Strong Edge
        50,                     # Threshold votes for Center Detection
        int(height * 0.25),     # Minimum Radius
        int(height * 0.46),     # Maximum Radius
    )
    # Average found circles, found it to be more accurate than trying to tune HoughCircles parameters to get just the right one
    a, b, c = circles.shape                 # (1) Get the no.of image in batch, (2) no. of circles detected, (3) x,y,radius
    x, y, r = avg_circles(circles, b)       # Get the average centroid

    # Draw Center and Circle
    cv2.circle(img, (x, y), r, (0, 0, 255), 3, cv2.LINE_AA)  # Draws Red Circle with thickness 3, 
     
    cv2.circle(img, (x, y), 2, (0, 255, 0), 3, cv2.LINE_AA)  # Draws Green Center of Circle

    # For Testing, Output Circles on Image
    image_filename_circle = output_path + "/{}_{}_circle.png".format(line_key, pump_key)
    cv2.imwrite(image_filename_circle, img)

    # For calibration, plot lines from center going out at every 10 degrees and add marker
    # For i from 0 to 36 (every 10 deg)

    """
    Goes through the motion of a circle and sets x and y values based on the set separation spacing.  Also adds text to each
    line.  These lines and text labels serve as the reference point for the user to enter
    NOTE: by default this approach sets 0/360 to be the +x axis (if the image has a cartesian grid in the middle), the addition
    (i+9) in the text offset rotates the labels by 90 degrees so 0/360 is at the bottom (-y in cartesian).  So this assumes the
    gauge is aligned in the image, but it can be adjusted by changing the value of 9 to something else.
    """

    separation = 10.0  # In degrees
    interval = int(360 / separation)
    p1 = np.zeros((interval, 2))  # Set empty arrays with 36 rows and 2 colums
    p2 = np.zeros((interval, 2))  
    p_text = np.zeros((interval, 2))


    # This loop builds a set of (x, y) points along a circular arc or full circle, 
    # and stores them in the p1 array.
    # Note: 0.9 is used as the area of interest is smaller than the full radius

    for i in range(0, interval):
        for j in range(0, 2):
            if j % 2 == 0:  # x-coordinates
                p1[i][j] = x + 0.9 * r * np.cos(
                    separation * i * 3.14 / 180
                )  
            else: # y-coordinates
                p1[i][j] = y + 0.9 * r * np.sin(separation * i * 3.14 / 180)

    # Text alignments
    text_offset_x = 10
    text_offset_y = 5

    # Plot Values outside the Angles
    # Plot the Text Labels
    # np.cos() provides the Horizontal Component, 
    # np.sin() provides the Vertical Component

    for i in range(0, interval):
        for j in range(0, 2):
            if j % 2 == 0: # x-coordinates
                p2[i][j] = x + r * np.cos(separation * i * 3.14 / 180)
                p_text[i][j] = (
                    x
                    - text_offset_x
                    + 1.2 * r * np.cos((separation) * (i + 9) * 3.14 / 180)
                )  # point for text labels, i+9 rotates the labels by 90 degrees

            else: # y-coordinates
                p2[i][j] = y + r * np.sin(separation * i * 3.14 / 180)
                p_text[i][j] = (
                    y
                    + text_offset_y
                    + 1.2 * r * np.sin((separation) * (i + 9) * 3.14 / 180)
                )  # point for text labels, i+9 rotates the labels by 90 degrees

    # Add the Lines and Labels to the Image
    for i in range(0, interval):

        # Plot the Dial Lines
        cv2.line(
            img,
            (int(p1[i][0]), int(p1[i][1])), # pt1: Starting Pt
            (int(p2[i][0]), int(p2[i][1])), # pt2: Ending Pt
            (0, 255, 0),                    # Green Color
            2,                              # Thickness
        )

        cv2.putText(
            img,
            "%s" % (int(i * separation)),            # string of i * (0-35)
            (int(p_text[i][0]), int(p_text[i][1])),  # position of label 
            cv2.FONT_HERSHEY_SIMPLEX,                # font
            0.3,                                     # font scale
            (0, 0, 0),                               # black
            1,                                       # thickness
            cv2.LINE_AA,                             # anti-aliasing (smooth)
        )

    # Store image
    image_filename_final = output_path + "/{}_{}_final.png".format(line_key, pump_key)
    cv2.imwrite(image_filename_final, img)

    # Min & Max Angles / Value
    min_angle = 47  # Lowest angle for gauge
    max_angle = 315 # Highest angle for gauge
    min_value = 0   # Minimum value for gauge
    max_value = 4   # Maximum value for gauge
    units = "psi"

    return min_angle, max_angle, min_value, max_value, units, x, y, r


def get_current_value(
    img,
    min_angle,
    max_angle,
    min_value,
    max_value,
    x,
    y,
    r,
    output_path,
    line_key,
    pump_key,
):
    # TEST CODE:
    # img = cv2.imread('gauge-%s.%s' % (gauge_number, file_type))

    gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Gray scaling

    # Set threshold and maxValue
    thresh = 50
    maxValue = 250

    # Apply thresholding which helps for finding lines
    # Returns, th: threshold used & dst2: thresholded image
    th, dst2 = cv2.threshold(gray2, thresh, maxValue, cv2.THRESH_BINARY_INV)

    # Store thresholded image
    image_filename_grey = output_path + "/{}_{}_grayscale.png".format(
        line_key, pump_key
    )
    cv2.imwrite(image_filename_grey, dst2)

    # Line Detection
    # Note: # rho is set to 3 to detect more lines, 
    # easier to get more then filter them out later
    minLineLength = 10
    maxLineGap = 0

    # Note: Each line is shaped [[x1,y1,x2,y2]]
    lines = cv2.HoughLinesP(
        image=dst2,                     # Single-Channel Binary Image
        rho=3,                          # Distance Resolution of Accumulator (Pixels)
        theta=np.pi / 180,              # Angle Resolution of Accumulator (Radians). 1 now.
        threshold=100,                  # Minimum number of intersections in Hough space 
        minLineLength=minLineLength,    # Minimum length accepted
        maxLineGap=0,                   # Maximum gap between lines to be considered single line
    )  

    # TEST CODE: show all found lines
    # for i in range(0, len(lines)):
    #   for x1, y1, x2, y2 in lines[i]:
    #      cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #      cv2.imwrite(output_path + "/" +'lines.jpg', img)

    # Remove all Lines outside a Given Radius
    # Note: diff1 controls length of line within Radius
    # Note: diff2 controls how close line is radius of circle

    final_line_list = []
    # print "radius: %s" %r
    # diff1LowerBound = 0.15
    diff1LowerBound = 0.00  # diff1LowerBound and diff1UpperBound determine how close the line should be from the center
    # diff1UpperBound = 0.25
    diff1UpperBound = 0.50
    # diff2LowerBound = 0.5
    diff2LowerBound = 0.5  # diff2LowerBound and diff2UpperBound determine how close the other point of the line should be to the outside of the gauge
    # diff2UpperBound = 1.0
    diff2UpperBound = 1

    line_length_lst = []
    line_pos_lst = []
    
    # Find the difference of lengths from center coordinates (x,y)
    for i in range(0, len(lines)):
        for x1, y1, x2, y2 in lines[i]:
            diff1 = dist_2_pts(x, y, x1, y1)  # x, y is center of circle
            diff2 = dist_2_pts(x, y, x2, y2)  # x, y is center of circle
            # set diff1 to be the smaller (closest to the center) of the two), makes the math easier

            # Swap diff1 and diff2 should diff1 > diff2
            if diff1 > diff2:
                temp = diff1
                diff1 = diff2
                diff2 = temp

            # Check if line is within an acceptable range
            if (
                (diff1 < diff1UpperBound * r)
                and (diff1 > diff1LowerBound * r)
                and (diff2 < diff2UpperBound * r)
            ) and (diff2 > diff2LowerBound * r):
                # if (((diff1<160) and (diff1>140) and (diff2<190)) and (diff2>170)):
                line_length = dist_2_pts(x1, y1, x2, y2)
                line_length_lst.append(line_length)
                # add to final list
                # final_line_list.append([x1, y1, x2, y2])
                line_pos_lst.append([x1, y1, x2, y2])

    # Jerrold
    print(line_length_lst)
    final_indx = line_length_lst.index(max(line_length_lst)) # Finds the position of the longest line
    final_line_list.append(line_pos_lst[final_indx]) # Appends final_line_list with the longest line

    # TEST CODE
    # testing only, show all lines after filtering
    # for i in range(0,len(final_line_list)):
    #     x1 = final_line_list[i][0]
    #     y1 = final_line_list[i][1]
    #     x2 = final_line_list[i][2]
    #     y2 = final_line_list[i][3]
    #     cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #     cv2.imwrite(output_path + "/" +'filter_lines.jpg', img)

    # Plots the line on the image
    # Note: It assumes the first line is the Best One
    x1 = final_line_list[0][0]
    y1 = final_line_list[0][1]
    x2 = final_line_list[0][2]
    y2 = final_line_list[0][3]
    cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # TEST CODE
    # for testing purposes, show the line overlayed on the original image
    # cv2.imwrite('gauge-1-test.jpg', img)

    # Draw the needle on the image
    image_filename_needle = output_path + "/{}_{}_needle.png".format(line_key, pump_key)
    cv2.imwrite(image_filename_needle, img)

    # Find the farthest point from the center to be what is used to determine the angle
    dist_pt_0 = dist_2_pts(x, y, x1, y1)
    print(x1)
    print(y1)
    print(x2)
    print(y2)
    print(dist_pt_0)

    dist_pt_1 = dist_2_pts(x, y, x2, y2)
    print(dist_pt_1)

    # Angle Calculation
    if dist_pt_0 > dist_pt_1:
        x_angle = x1 - x    # x-offset
        print(x1)
        print(x)
        print(x_angle)
        y_angle = y - y1    # y-offset
        print(y_angle)
    else:
        x_angle = x2 - x
        y_angle = y - y2

    # Take the arc tan of y/x to find the angle
    res = np.arctan(np.divide(float(y_angle), float(x_angle)))
    print(res)
    # np.rad2deg(res) #coverts to degrees

    # print x_angle
    # print y_angle
    # print res
    # print np.rad2deg(res)

    # Compensation as arc tan does not handle quadrants properly
    # Note: these were determined by trial and error
    res = np.rad2deg(res)
    if x_angle > 0 and y_angle > 0:  # in quadrant I
        final_angle = 270 - res
    if x_angle < 0 and y_angle > 0:  # in quadrant II
        final_angle = 90 - res
    if x_angle < 0 and y_angle < 0:  # in quadrant III
        final_angle = 90 - res
    if x_angle > 0 and y_angle < 0:  # in quadrant IV
        final_angle = 270 - res

    # TEST CODE
    # print final_angle

    # Linear Mapping to get the Value
    old_min = float(min_angle) # 47
    old_max = float(max_angle) # 315

    new_min = float(min_value) # 0
    new_max = float(max_value) # 4

    old_value = final_angle

    old_range = old_max - old_min # 268
    new_range = new_max - new_min # 4
    new_value = (((old_value - old_min) * new_range) / old_range) + new_min

    print(new_value)
    return new_value

def main(
    filepath,
    output_path,
    line_key,
    pump_key,
):
    try:
        # name the calibration image of your gauge 'gauge-#.jpg', for example 'gauge-5.jpg'.  It's written this way so you can easily try multiple images
        min_angle, max_angle, min_value, max_value, units, x, y, r = calibrate_gauge(
            filepath, output_path, line_key, pump_key
        )
        # feed an image (or frame) to get the current value, based on
        # the calibration, by default uses same image as calibration
        # img = cv2.imread('gauge-%s.%s' % (gauge_number, file_type))

        # img = cv2.imread('images\gauge-%s.%s' % (gauge_number, file_type))
        images = np.array(Image.open(filepath))

        img = cv2.resize(images, dsize=(271, 262), interpolation=cv2.INTER_CUBIC)

        val = get_current_value(
            img,
            min_angle,
            max_angle,
            min_value,
            max_value,
            x,
            y,
            r,
            output_path,
            line_key,
            pump_key,
        )

        format_float = "{:.2f}".format(val) # 2 significant figures
        print("------result--------")
        print(format_float)
        return format_float
    
    except Exception as e:
        raise e


if __name__ == "__main__":
    fp = r"C:\Users\j112i8272\Desktop\Python\nandar_pressure\output\2023_04_25_09_56_36\201_PRESSURE_PUMP_1_cropped.png"
    main(fp)
