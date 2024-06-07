const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const jwt = require('jsonwebtoken');

exports.handler = async (event) => {
    try {
        // 解析外层请求体
        const outerBody = JSON.parse(event.body);
        const encodedImage = outerBody.to_upload_image;
        const headers = event.headers;
        const method = event.method;
        const path = event.path;

        if (method !== 'POST' || path !== '/upload') {
            throw new Error('Invalid request');
        }

        // 从Authorization头中提取ID Token
        const authHeader = headers.Authorization || headers.authorization;

        if (!authHeader) {
            throw new Error('Authorization header is missing');
        }

        const idToken = authHeader.split(' ')[1];

        // 解码ID Token
        const decodedToken = jwt.decode(idToken);

        // 提取用户的email
        const userEmail = decodedToken.email;

        if (!userEmail) {
            throw new Error('Email not found in token');
        }

        const decodedImage = Buffer.from(encodedImage, 'base64');

        const params = {
            Bucket: "fit5225-group91-original",
            Key: `${userEmail}/${Date.now()}.jpg`, // 使用email和时间戳作为S3对象的Key
            Body: decodedImage,
            ContentType: "image/jpeg"
        };

        const data = await s3.upload(params).promise();

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            body: JSON.stringify({
                message: "Image uploaded successfully!",
                data: data
            })
        };
    } catch (err) {
        console.error('Error:', err);
        return {
            statusCode: 500,
            headers: {
                "Content-Type": "application/json",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            body: JSON.stringify({
                message: "Failed to upload image",
                error: err.message,
            })
        };
    }
};