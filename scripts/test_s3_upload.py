import os

from apps.shared.infrastructure.services.s3_service import S3Service  # adjust path if different


def test_s3_upload():
    s3 = S3Service()

    # Path to a sample file (create a temp file for testing)
    test_file_path = "property.jpeg"
    with open(test_file_path, "w") as f:
        f.write("This is a test upload to S3!")

    # Define where it should go in your bucket
    key = "test-folder/test_upload.txt"

    try:
        url = s3.upload_file(test_file_path, key, content_type="text/plain")
        print("✅ Upload successful!")
        print("File URL:", url)

        # Optionally test generating a presigned URL
        presigned = s3.generate_presigned_url(key)
        print("Presigned URL (valid for 1 hour):", presigned)
    except Exception as e:
        print("❌ Upload failed:", e)
    finally:
        # Clean up local file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


test_s3_upload()
