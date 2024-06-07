const AWS = require('aws-sdk');
const s3 = new AWS.S3();

exports.handler = async (event) => {
    try {
        const body = JSON.parse(event.body);
        const encodedImage = body.to_upload_image;
        const decodedImage = Buffer.from(encodedImage, 'base64');

        const params = {
            Bucket: "fit5225-group91-original",
            Key: `${Date.now()}.jpg`,
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
        return {
            statusCode: 500,
            body: JSON.stringify({
                message: "Failed to upload image",
                error: err.message,
            })
        };
    }
};