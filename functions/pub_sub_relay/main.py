import logging
import base64

import time
import os

from google.cloud import pubsub_v1

project_id = os.environ['TARGET_PROJECT_ID']
topic_name = os.environ['TOPIC_NAME']

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)


def callback(message_future):
    # When timeout is unspecified, the exception method waits indefinitely.
    if message_future.exception(timeout=30):
        logging.info('Publishing message on {} threw an Exception {}.'.format(
            topic_name, message_future.exception()))
    else:
        print(message_future.result())


def relay_pubsub_backup_trigger_func(data, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         data (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    logging.basicConfig(level=logging.info)

    if 'data' in data:
        pubsub_message = base64.b64decode(data['data'])
        logging.info('Python Pub/Sub receive_pubsub_backup_trigger_func function received message %s.', pubsub_message)

        message_future = publisher.publish(topic_path, data=pubsub_message)
        message_future.add_done_callback(callback)

        # We must keep the main thread from exiting to allow it to process
        # messages in the background.
        time.sleep(60)
