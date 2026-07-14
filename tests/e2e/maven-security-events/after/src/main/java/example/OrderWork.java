package example;

import jakarta.annotation.Resource;
import jakarta.enterprise.concurrent.ManagedExecutorService;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Event;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;

@ApplicationScoped
public class OrderWork {
    @Resource(lookup = "java:comp/DefaultManagedExecutorService")
    ManagedExecutorService executor;

    @Inject
    Event<OrderProcessed> events;

    public void process(String owner) {
        executor.submit(() -> events.fire(new OrderProcessed(owner)));
    }

    void observe(@Observes OrderProcessed event) {
        event.owner();
    }

    record OrderProcessed(String owner) {}
}
