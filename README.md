# PaintedDogBackend

This Repository Contains a Few Folders

First the StandAlone_Scripts Folder contains scripts to be run on their own, this contain things such as the script to upload all of the dog pictures to AWS as well as the script to run the entire database through the image processing pipeline

Second the AWSLambda Folder contains all of the Lambda Function in use on the website including the function to add a picture to the database upon upload and the function to process the image once uploaded. These lambda function are all managed by Serverless they are a mix of JS and Python. 

This the models folder will contain all versions of the trained dog classification models so far.

Each script or function will have its use explained in the header comments. 