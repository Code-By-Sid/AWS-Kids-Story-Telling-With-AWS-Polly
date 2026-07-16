import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

# ==========================================
# AWS Clients
# ==========================================

s3 = boto3.client("s3")
polly = boto3.client("polly")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("StoryLibrary")

# ==========================================
# Configuration
# ==========================================

TEXT_BUCKET = "story-text-buc-ket"
AUDIO_BUCKET = "story-audio-buc-ket"

VOICE_ID = "Joanna"
LANGUAGE = "en-US"

# ==========================================
# Decimal JSON Serializer
# ==========================================

def decimal_default(obj):

    if isinstance(obj, Decimal):
        return float(obj)

    raise TypeError


# ==========================================
# API Response
# ==========================================

def response(status, body):

    return {

        "statusCode": status,

        "headers": {

            "Content-Type": "application/json"

        },

        "body": json.dumps(
            body,
            default=decimal_default
        )

    }


# ==========================================
# Lambda Handler
# ==========================================

def lambda_handler(event, context):

    try:

        method = event["requestContext"]["http"]["method"]

        path = event["rawPath"]

        print("Method :", method)

        print("Path :", path)

        # ==========================================
        # POST /upload
        # ==========================================

        if method == "POST" and path.endswith("/upload"):

            body = json.loads(event["body"])

            filename = body["filename"]

            story_text = body["story"]

            # Upload story to S3

            s3.put_object(

                Bucket=TEXT_BUCKET,

                Key=filename,

                Body=story_text.encode("utf-8"),

                ContentType="text/plain"

            )

            print("Story uploaded successfully.")

            # Read story back from S3

            obj = s3.get_object(

                Bucket=TEXT_BUCKET,

                Key=filename

            )

            story_text = obj["Body"].read().decode("utf-8")

            print("Story loaded from S3")

            story_url = (
                f"https://{TEXT_BUCKET}.s3.amazonaws.com/{filename}"
            )
            # ==========================================
            # Amazon Polly
            # ==========================================

            print("Generating MP3...")

            polly_response = polly.synthesize_speech(

                Text=story_text,

                OutputFormat="mp3",

                VoiceId=VOICE_ID

            )

            audio_stream = polly_response["AudioStream"].read()

            mp3_name = filename.replace(".txt", ".mp3")

            # Upload MP3 to S3

            s3.put_object(

                Bucket=AUDIO_BUCKET,

                Key=mp3_name,

                Body=audio_stream,

                ContentType="audio/mpeg"

            )

            print("MP3 Uploaded Successfully")

            audio_url = (
                f"https://{AUDIO_BUCKET}.s3.amazonaws.com/{mp3_name}"
            )

            # ==========================================
            # Story Statistics
            # ==========================================

            word_count = len(story_text.split())

            character_count = len(story_text)

            reading_time = round(word_count / 200, 2)

            print("Word Count :", word_count)

            print("Character Count :", character_count)

            print("Reading Time :", reading_time, "Minutes")

            # ==========================================
            # Store in DynamoDB
            # ==========================================

            table.put_item(

                Item={

                    "StoryId": str(uuid.uuid4()),

                    "StoryName": filename,

                    "StoryText": story_text,

                    "StoryURL": story_url,

                    "AudioURL": audio_url,

                    "Voice": VOICE_ID,

                    "Language": LANGUAGE,

                    "WordCount": word_count,

                    "CharacterCount": character_count,

                    "ReadingTime": f"{reading_time} Minutes",

                    "Timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                }

            )

            print("Story Details Saved Successfully")

            return response(

                200,

                {

                    "message": "Story Uploaded Successfully",

                    "storyName": filename,

                    "storyURL": story_url,

                    "audioURL": audio_url,

                    "voice": VOICE_ID,

                    "language": LANGUAGE,

                    "wordCount": word_count,

                    "characterCount": character_count,

                    "readingTime": f"{reading_time} Minutes"

                }

            )
        # ==========================================
        # GET /stories
        # ==========================================

        elif method == "GET" and path.endswith("/stories"):

            response_db = table.scan()

            items = response_db.get("Items", [])

            stories = []

            for item in items:

                stories.append(

                    {

                        "storyId": item["StoryId"],

                        "storyName": item["StoryName"],

                        "storyText": item["StoryText"],

                        "storyURL": item["StoryURL"],

                        "audioURL": item["AudioURL"],

                        "voice": item["Voice"],

                        "language": item["Language"],

                        "wordCount": int(item["WordCount"]),

                        "characterCount": int(item["CharacterCount"]),

                        "readingTime": item["ReadingTime"],

                        "timestamp": item["Timestamp"]

                    }

                )

            print("===================================")

            print("Total Stories :", len(stories))

            print("===================================")

            return response(

                200,

                {

                    "stories": stories

                }

            )

        # ==========================================
        # Invalid Route
        # ==========================================

        else:

            return response(

                404,

                {

                    "message": "Invalid Route"

                }

            )

    except Exception as e:

        print("ERROR :", str(e))

        return response(

            500,

            {

                "error": str(e)

            }

        )