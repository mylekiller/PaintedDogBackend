import os
import cv2
import boto3
import numpy
from tqdm import *
import math
import botocore


def walkdir(folder):
    """Walk through each files in a directory"""
    for dirpath, dirs, files in os.walk(folder):
        for filename in files:
            yield dirpath+'/'+filename

def resizeImage(img, TARGET_PIXEL_AREA=160000.0):
	"""Get the aspect ratio of the image"""
	ratio = float(img.shape[1]) / float(img.shape[0])
	"""Calculate the new height"""
	new_h = int(math.sqrt(TARGET_PIXEL_AREA / ratio) + 0.5)
	"""Calculate the new width"""
	new_w = int((new_h * ratio) + 0.5)
	"""Perform the Resize"""
	return cv2.resize(img, (new_w,new_h))

s3 = boto3.resource('s3')

rootDir = 'PaintedDogsProject'

filecounter = 0
for path in walkdir(rootDir):
	filecounter += 1

for file in tqdm(walkdir(rootDir), total=filecounter, unit="files"):
	if file.split('/')[-1][0] != ".":
		Key=file.split('/')[1].split(' ')[0].lower()+'/'+file.split('/')[2].lower()+'/'+file.split('/')[3].lower()
		try:
			s3.Object('ndpainteddogs', Key).load()
		except botocore.exceptions.ClientError as e:
			if e.response['Error']['Code'] == "404":
				img = cv2.imread(file)
				rimg = resizeImage(img)
				almost = cv2.imencode('.'+file.split('.')[-1],rimg)[1].tostring()
				tqdm.write(Key)
				s3.Bucket('ndpainteddogs').put_object(Key=file.split('/')[1].split(' ')[0].lower()+'/'+file.split('/')[2].lower()+'/'+file.split('/')[3].lower(), Body=almost)
			else:
				tqdm.write("Some other error")
		#img = cv2.imread(file)
		#rimg = resizeImage(img)
		#almost = cv2.imencode('.'+file.split('.')[-1],rimg)[1].tostring()
		#tqdm.write(Key)
		#objs = list(s3.Bucket('ndpainteddogs').objects.filter(Prefix=Key))
		#if len(objs) > 0 and objs[0].key == Key:
		#	pass
		#else:
		#	s3.Bucket('ndpainteddogs').put_object(Key=file.split('/')[1].split(' ')[0]+'/'+file.split('/')[2]+'/'+file.split('/')[3], Body=almost)
