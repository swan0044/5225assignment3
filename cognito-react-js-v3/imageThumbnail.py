import boto3
import cv2
import numpy as np
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # 获取上传的文件信息
    source_bucket = 'fit5225-group91-original'
    source_key = event['Records'][0]['s3']['object']['key']
    target_bucket = 'fit5225-group91-thumbnail'
    target_key = 'thumbnails/' + source_key
    
    # 下载图像文件
    download_path = '/tmp/{}{}'.format(source_key, os.path.splitext(source_key)[-1])
    s3.download_file(source_bucket, source_key, download_path)
    
    # 使用 OpenCV 生成缩略图
    image = cv2.imread(download_path)
    height, width = image.shape[:2]
    thumbnail_size = (100, int((100/width) * height))
    thumbnail = cv2.resize(image, thumbnail_size, interpolation=cv2.INTER_AREA)
    thumbnail_path = '/tmp/thumbnail-{}'.format(source_key)
    cv2.imwrite(thumbnail_path, thumbnail)
    
    # 上传缩略图到目标 S3 bucket
    s3.upload_file(thumbnail_path, target_bucket, target_key)
    
    return {
        'statusCode': 200,
        'body': f'Thumbnail created and uploaded to {target_bucket}/{target_key}'
    }