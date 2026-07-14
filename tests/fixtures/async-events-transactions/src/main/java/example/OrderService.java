package example;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.retry.annotation.Retryable;
import org.springframework.scheduling.annotation.Async;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

class OrderService {
    ApplicationEventPublisher events;

    @Async("ordersExecutor")
    @Retryable(maxAttempts = 4)
    @Transactional(propagation = Propagation.REQUIRES_NEW, timeout = 5)
    void submit() {
        events.publishEvent(new Object());
    }
}
