package example.worker;

import org.springframework.kafka.annotation.KafkaListener;

class OrderConsumer {
    @KafkaListener(topics = "orders", groupId = "enterprise-worker")
    void receive(String order) {
        // Baseline fixture: the migration must characterize acknowledgment and failure behavior.
    }
}
