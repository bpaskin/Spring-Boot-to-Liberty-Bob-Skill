package example;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;

interface TodoRepository extends JpaRepository<Todo, Long> {}

@Controller
class TodoController {
    @PostMapping("/todos")
    String create() {
        return "redirect:/todos";
    }
}

class Todo {}
