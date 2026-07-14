package example;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
class LegacyController {
    @GetMapping("/legacy")
    String legacy() { return "legacy"; }
}
