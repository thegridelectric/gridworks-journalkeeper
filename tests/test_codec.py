

s3_object = self.s3.get_object(
            Bucket=self.aws_bucket_name, Key=file_name_meta.file_name
        )