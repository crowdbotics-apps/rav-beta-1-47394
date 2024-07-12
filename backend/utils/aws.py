
import boto3
from botocore.exceptions import NoCredentialsError

# Your modified function to generate a signed URL
def generate_signed_url(bucket_name, object_key, access_key_id, secret_access_key, region_name):
    try:
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name
        )

        s3_client = session.client('s3')
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=3600
        )

        return url

    except NoCredentialsError:
        return None
