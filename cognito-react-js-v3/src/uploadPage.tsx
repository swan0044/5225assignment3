import React, { useState } from 'react';

const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first!');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64Image = (reader.result as string).split(',')[1]; // 确保去掉前缀
      const body = JSON.stringify({
        body: JSON.stringify({ to_upload_image: base64Image }),
        headers: {
          "Content-Type": "application/json"
        },
        httpMethod: "POST",
        path: "/image-upload"
      });

      try {
        const response = await fetch('https://4h60uq9dkf.execute-api.us-east-1.amazonaws.com/dev/upload', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: body
        });
        const data = await response.json();
        setMessage('Upload successful');
      } catch (error) {
        setMessage('Upload failed');
      }
    };

    reader.readAsDataURL(file);
  };

  return (
    <div>
      <h1>Upload Image</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {message && <p>{message}</p>}
    </div>
  );
};

export default UploadPage;