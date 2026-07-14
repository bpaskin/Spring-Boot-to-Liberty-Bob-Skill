package example;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
class StatusController {
    @GetMapping("/status")
    String status() { return "ok"; }
}
