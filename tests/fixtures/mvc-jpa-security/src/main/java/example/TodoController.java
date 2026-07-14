package example;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
class TodoController {
    @GetMapping("/todos")
    String todos(Model model) {
        return "todos";
    }
}
