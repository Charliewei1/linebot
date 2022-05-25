import boto3#最初のアップロードや確認用。
#Lambdaではない場所で実行しているので権限周りの設定がいらないっぽい？
s3 = boto3.resource('s3')
bucket = s3.Bucket('wikilist')
#bucket.upload_file('test.csv', 'test.csv')
bucket.download_file('test.csv', 'test.csv')