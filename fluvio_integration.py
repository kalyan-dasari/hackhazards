from fluvio import Fluvio

fluvio = Fluvio.connect()

def send_message(topic, message):
    producer = fluvio.topic_producer(topic)
    producer.send_string(message)

def consume_messages(topic):
    consumer = fluvio.topic_consumer(topic)
    return consumer.stream()
