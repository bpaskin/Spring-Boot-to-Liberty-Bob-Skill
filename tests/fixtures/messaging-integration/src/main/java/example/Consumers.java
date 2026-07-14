package example;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.kafka.annotation.KafkaListener;

class Consumers {
    @KafkaListener(topics = "orders", groupId = "billing")
    void kafka(String value) {}

    @RabbitListener(queues = "notifications")
    void rabbit(String value) {}
}
