package example;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@FeignClient(name = "inventory")
interface InventoryClient {}

interface ItemRepository extends ReactiveCrudRepository<Item, Long> {}

record Item(Long id) {}

@RestController
class ReactiveGateway {
    @GetMapping("/items")
    Flux<Item> items() { return Flux.empty(); }
}
