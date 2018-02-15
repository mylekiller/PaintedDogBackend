import os
import cv2
import boto3
import numpy as np
from tqdm import *
import math
import botocore

def walkdir(folder):
    """Walk through each files in a directory"""
    for dirpath, dirs, files in os.walk(folder):
        for directory in dirs:
            yield dirpath+'/'+directory

# Load in all the AWS Resources we will be using
s3 = boto3.resource('s3')
db = boto3.resource('dynamodb')

rootDir = 'PaintedDogsProject'

filecounter = 0
for path in walkdir(rootDir):
	filecounter += 1

for file in tqdm(walkdir(rootDir), total=filecounter, unit="files"):
	if file.split('/')[-1][0] != ".":
		if len(file.split('/')) == 3:
			packname = file.split('/')[1].split(' ')[0].lower()
			dogname = file.split('/')[2].lower()
			# Get the specific Item of interest (Will probably trigger on database update in order to be able to process each image)
			table = db.Table('dogs')
			item = table.get_item(Key={"packName": packname, "dogName": dogname})

			# Once you have the item you can see all of the pictures attached to that dog
			dogs = item['Item']['picture']

			for dog in dogs:

				# Retrieve the picture of interest from the S3 Bucket
				obj = s3.Object(bucket_name='ndpainteddogs', key='processed/'+packname+'/'+dogname+'/'+dog)
				response = obj.get()
				data = response['Body'].read()
				
				# Load the image of interest into OpenCV
				nparr = np.fromstring(data, np.uint8)
				img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

				# TODO: Figure out if resizing should happen here or should the images already be resized?
				height, width = img.shape[:2]
				# Get the resized height and width
				h, w = img.shape[:2]

				# Load the image into a blob to be used in the Neural Network
				blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
				# Set the input
				net.setInput(blob)
				# Run the Neural Network
				detections = net.forward()
				# Focus on the detections that are most likely to be a dog
				for i in np.arange(0, detections.shape[2]):
					confidence = detections[0, 0, i, 2]
					if confidence > 0.2:
						idx = int(detections[0, 0, i, 1])
						# only focus on detections that are of type Dog or Horse
						if idx == 12 or idx == 13:
							box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
							(startX, startY, endX, endY) = box.astype("int")
				
				# Create a copy of the image in order preserve the original (if ever needed)
				img2 = img.copy()	
				img2 = img2[startY:endY, startX:endX]
				h, w = img2.shape[:2]						   
				# Create a black mask that will cover the background of the image in black
				mask = np.zeros(img.shape[:2], dtype = np.uint8) 
				output = np.zeros(img.shape, np.uint8)		   
				# Set the starting rectangle to the bounding box that the Neural Network outputs
				rect = (0, 0, h, w)	
				# Set up the background and foreground pixels models but these wont be used yet			
				bgdmodel = np.zeros((1, 65), np.float64)
				fgdmodel = np.zeros((1, 65), np.float64)
				# Run cutgrab and pray that it makes a good cut of the Dog from the Background
				cv2.grabCut(img2, mask, rect, bgdmodel, fgdmodel, 5, cv2.GC_INIT_WITH_RECT)
				# Mask the image to cut out parts that are not part of the dog
				mask2 = np.where((mask==1) + (mask==3),255,0).astype('uint8')
				output = cv2.bitwise_and(img2,img2,mask=mask2)
				# Write the finished image to disk 
				almost = cv2.imencode('.'+dog.split('.')[1],output)[1].tostring()

				# Write the saved image to S3 and (maybe update the database?)
				s3.Bucket('ndpainteddogs').put_object(Key='processed/'+packname+'/'+dogname+'/'+dog, Body=almost)

