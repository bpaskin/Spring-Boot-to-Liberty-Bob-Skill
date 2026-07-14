package example;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.scheduling.annotation.Async;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;

@Service
class LegacyService {
    private final ApplicationEventPublisher events;

    LegacyService(ApplicationEventPublisher events) {
        this.events = events;
    }

    @Async("ordersExecutor")
    @PreAuthorize("hasRole('ADMIN') or authentication.name == #owner")
    void process(String owner) {
        events.publishEvent(new OrderProcessed(owner));
    }

    record OrderProcessed(String owner) {}
}
