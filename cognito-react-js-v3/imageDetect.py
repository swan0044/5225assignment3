import boto3
import cv2
import numpy as np
import os
import json
from collections import Counter

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# 自定义部分：DynamoDB 表名称
table = dynamodb.Table("ImageMetadata")

# YOLO 配置
yolo_path = "/tmp/yolo"  # 临时路径，用于存储从 S3 下载的 YOLO 文件
labels_path = "coco.names"
config_path = "yolov3-tiny.cfg"
weights_path = "yolov3-tiny.weights"
conf_threshold = 0.3
nms_threshold = 0.1
accuracy_threshold = 0.6  # 忽略检测准确率低于此值的对象

# 自定义部分：S3 bucket 名称
yolo_bucket_name = "fit5225-group91-yolo"
original_bucket_name = "fit5225-group91-original"
thumbnail_bucket_name = "fit5225-group91-thumbnail"


# 从 S3 下载 YOLO 配置文件和权重
def download_yolo_files():
    s3.download_file(
        yolo_bucket_name,
        "yolo_tiny_configs/coco.names",
        os.path.join(yolo_path, labels_path),
    )
    s3.download_file(
        yolo_bucket_name,
        "yolo_tiny_configs/yolov3-tiny.cfg",
        os.path.join(yolo_path, config_path),
    )
    s3.download_file(
        yolo_bucket_name,
        "yolo_tiny_configs/yolov3-tiny.weights",
        os.path.join(yolo_path, weights_path),
    )


# 加载 YOLO 模型
def load_model():
    labels = open(os.path.join(yolo_path, labels_path)).read().strip().split("\n")
    net = cv2.dnn.readNetFromDarknet(
        os.path.join(yolo_path, config_path), os.path.join(yolo_path, weights_path)
    )
    return labels, net


# 执行对象检测
def do_prediction(image, net, labels):
    (H, W) = image.shape[:2]
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layer_outputs = net.forward(ln)

    boxes = []
    confidences = []
    class_ids = []

    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > conf_threshold:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
    tag_counter = Counter()  # 使用 Counter 来统计标签

    if len(idxs) > 0:
        for i in idxs.flatten():
            if confidences[i] >= accuracy_threshold:  # 只保留检测准确率高于阈值的对象
                tag_counter[labels[class_ids[i]]] += 1

    return dict(tag_counter)  # 转换为字典以进行 JSON 序列化


def lambda_handler(event, context):
    try:
        # 创建临时目录
        if not os.path.exists(yolo_path):
            os.makedirs(yolo_path)

        # 下载 YOLO 文件
        download_yolo_files()

        # 加载模型
        labels, net = load_model()

        # 获取上传的文件信息
        source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
        source_key = event["Records"][0]["s3"]["object"]["key"]

        # 提取原图的 key（缩略图路径是 'thumbnails/'，去掉前缀以获得原图的 key）
        original_key = source_key.replace("thumbnails/", "")
        download_path = "/tmp/{}".format(original_key)

        # 下载原图文件
        s3.download_file(original_bucket_name, original_key, download_path)

        # 读取图像文件
        image = cv2.imread(download_path)

        # 进行对象检测
        tags = do_prediction(image, net, labels)

        # 获取原图 S3 URL
        image_url = f"s3://{original_bucket_name}/{original_key}"

        # 获取缩略图 HTTP URL
        thumbnail_url = f"https://{thumbnail_bucket_name}.s3.amazonaws.com/{source_key}"

        # 将标签字典转换为 JSON 字符串
        tags_json = json.dumps(tags)

        # 保存元数据到 DynamoDB
        table.put_item(
            Item={
                "ImageID": original_key,
                "Tags": tags_json,
                "ImageURL": image_url,
                "ThumbnailURL": thumbnail_url,
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps("Object detection completed and metadata saved."),
        }
    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": json.dumps(str(e))}
