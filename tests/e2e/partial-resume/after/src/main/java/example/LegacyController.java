package example;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

// TODO: Migration required — retained by the confirmed staged slice.
@RestController
class LegacyController {
    @GetMapping("/legacy")
    String legacy() { return "legacy"; }
}
