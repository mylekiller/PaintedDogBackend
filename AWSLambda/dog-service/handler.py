import numpy as np 
import cv2
import boto3
import os

def process(event, context):
	# Load in all the AWS Resources we will be using
	s3 = boto3.resource('s3')
	db = boto3.resource('dynamodb')

	for record in event['Records']:
		packname = record['dynamodb']['Keys']['packName']['S']
		dogname = record['dynamodb']['Keys']['dogName']['S']
		if record['eventName'] == 'MODIFY':
			oldPictureList = record['dynamodb']['OldImage']['picture']['L']
		newPictureList = record['dynamodb']['NewImage']['picture']['L']

		if record['eventName'] == 'MODIFY':
			oldsize = len(oldPictureList)
		else:
			oldsize = 0

		newsize = len(newPictureList)


		for dog in newPictureList[oldsize:newsize]:

			dog = dog['S']
			# Retrieve the picture of interest from the S3 Bucket
			obj = s3.Object(bucket_name='ndpainteddogs', key=packname+'/'+dogname+'/'+dog)
			response = obj.get()
			data = response['Body'].read()

			# Load in our trained Convolution Network in order to draw a bounding box around our dog
			net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt.txt", "MobileNetSSD_deploy.caffemodel")
			
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
			
			if 'startX' not in locals():
				startX = 5
				startY = 5
				endX   = width-5
				endY   = height-5
			# Create a copy of the image in order preserve the original (if ever needed)
			img2 = img.copy()							   
			# Create a black mask that will cover the background of the image in black
			mask = np.zeros(img.shape[:2], dtype = np.uint8) 
			output = np.zeros(img.shape, np.uint8)		   
			# Set the starting rectangle to the bounding box that the Neural Network outputs
			rect = (startX, startY, endX, endY)	
			# Set up the background and foreground pixels models but these wont be used yet			
			bgdmodel = np.zeros((1, 65), np.float64)
			fgdmodel = np.zeros((1, 65), np.float64)
			# Run cutgrab and pray that it makes a good cut of the Dog from the Background
			cv2.grabCut(img2, mask, rect, bgdmodel, fgdmodel, 5, cv2.GC_INIT_WITH_RECT)
			# Mask the image to cut out parts that are not part of the dog
			mask2 = np.where((mask==1) + (mask==3),255,0).astype('uint8')
			output = cv2.bitwise_and(img2,img2,mask=mask2)
			# Write the finished image to disk 
			almost = cv2.imencode('.'+dog.split('.')[-1],output)[1].tostring()

			# Write the saved image to S3 and (maybe update the database?)
			s3.Bucket('ndpainteddogs').put_object(Key='processed/'+packname+'/'+dogname+'/'+dog, Body=almost)

