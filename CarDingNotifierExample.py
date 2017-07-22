#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 14:31:35 2017

@author: markditsworth
"""

import os
import json
import smtplib
import requests
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# File path with images: to be set as working directory
img_fp = '/path/to/images'

# File path for license plate recognition response: relative to img_fp
lp_response_path = "path/to/response/json"

#phone number for notification
phone = 5555555555

# Microsoft Azure Face API Subscription Key
KEY = 'Face API Key'

# openALPR Subscription Key
ALPR_KEY = 'openALPR Key'

# Returns number of faces detected in an image
def getFace(fp):
    headers = {'Content-Type': 'application/octet-stream',
               'Ocp-Apim-Subscription-Key':KEY}
    url = 'https://westus.api.cognitive.microsoft.com/face/v1.0/detect'
    
    # open image as binary
    data = open(fp,'rb')
    
    # send POST Request
    resp = requests.post(url,data=data,headers=headers)
    
    # return length of response (# of faces detected in picture)
    return len(resp.json())

# Returns the closest license plate number in an image
def getPlates(fp):
    # cURL POST to openALPR API, store json response in lp_response_path
    bashcommand = 'curl -X POST -H "Content-Type: multipart/form-data" -H "Accept: application/json" -F "image=@{}" "https://api.openalpr.com/v2/recognize?secret_key={}&recognize_vehicle=0&country=us&return_image=0&topn=3" > {}'.format(fp,ALPR_KEY,lp_response_path)
    os.system(bashcommand)
    
    max_area = 0
    plate = ""
    
    # read openALPR response
    with open(lp_response_path) as res:
        data = json.load(res)
    
    # Parse response for license plates
    for x in data['results']:
        # Identify largest (nearest) plate in image
        area = x['vehicle_region']['height'] * x['vehicle_region']['width']
        if area > max_area:
            max_area = area
            plate = x['plate']
            
    return plate

# Sends text message through email
def notify2(message,number):
    # Define Addresses
    fromaddr = "emailaccount@gmail.com"
    # AT&T text only
    #toaddr = "{}@txt.att.net".format(str(number))
    
    # AT&T with picture
    #toaddr = "{}@mms.att.net".format(str(number))
    
    # Verizon text only
    #toaddr = "{}@vtext.com".format(str(number))
    
    # Verizon with picture
    toaddr = "{}@vzwpix.com".format(str(number))
    
    # T-Mobile text only
    #toaddr = "{}@tmomail.net".format(str(number))
    
    # Sprint text only
    #toaddr = "{}@messaging.sprintpcs.com".format(str(number))
    
    # Sprint with picture
    #toaddr = "{}@pm.sprint.com".format(str(number))
    
    #Initialize Email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = 'Accident Notification'
    
    body = "Your car may have been hit.\n\n" + message
    
    msg.attach(MIMEText(body,'plain'))
    
    if message != "":
        # Attache Image
        #filename = 'H3.jpg'
        #attachment = open(filename,'rb')
        #part = MIMEBase('application','octet-stream')
        #part.set_payload((attachment).read())
        #encoders.encode_base64(part)
        #part.add_header('Content-Disposition', "attachment; filename= %s" %filename)
        #msg.attach(part)
    
    # Log into email account and send email
    server = smtplib.SMTP(host='smtp.gmail.com',port=587)
    server.ehlo()
    server.starttls()
    server.login(fromaddr,"password")
    mes = msg.as_string()
    server.sendmail(fromaddr,toaddr,mes)
    server.quit()

def main():
    # set working directory as directory with stored images
    os.chdir(img_fp)
    
    # get list of all files in directory
    files = os.listdir(os.getcwd())
    
    # initialize Plate and Face arrays
    Plates = [0] * len(files)
    Faces = [0] * len(files)
    
    # initialize DataFrame
    df = pd.DataFrame({'Files':files,'Plates':Plates,'Faces':Faces})
    df = df.set_index('Files')
    
    # for every JPG image
    for f in files:
        if f == '.DS_Store':
            continue
        
        print(f)
        # get nearest license plate in picture
        plate = getPlates(f)
        # store plate number in corresponding dataframe location (if applicable)
        if plate:
            df.loc[f,'Plates'] = plate
        # get number of faces in picture
        face = getFace(f)
        # store number of faces in corresponding dataframe location
        if face:
            df.loc[f,'Faces'] = face
    
    # get list of JPG images that have faces in them
    has_face = df[df.loc[:,'Faces'] != 0]
    has_face = has_face.index.values.tolist()
    
    # get list of JPG images that have a license plate number in them
    plate_list = df[df.loc[:,'Plates'] != 0]
    plate_list = plate_list.loc[:,'Plates'].unique()
    msg = ""
    if len(plate_list) > 0:
        # create message listing the license plates in detected
        plate_msg = "The following plates were near your car:\n"
        for x in plate_list:
            plate_msg = plate_msg + str(x) + "\n"
        msg = msg + plate_msg
    
    if len(has_face) > 0:
        # add list of images that contain faces
        face_msg = "The following images contain faces nearby:\n"
        for x in has_face:
            face_msg = face_msg + str(x) + "\n"
        msg = msg + face_msg
    
    
    # send notification message to the phone number
    notify2(msg,phone)

if __name__ == "__main__":
    main()