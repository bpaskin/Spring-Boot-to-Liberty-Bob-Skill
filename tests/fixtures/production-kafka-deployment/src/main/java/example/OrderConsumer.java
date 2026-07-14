package example;

import org.springframework.kafka.annotation.KafkaListener;

class OrderConsumer {
    @KafkaListener(topics = "orders", groupId = "fulfillment")
    void consume(String event) {}
}
