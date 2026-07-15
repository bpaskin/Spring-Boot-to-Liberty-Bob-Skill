package example;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.InitBinder;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.WebDataBinder;

@Controller
class TodoController {
    @InitBinder("todoForm")
    void bindTodo(WebDataBinder binder) {
        binder.setAllowedFields("title");
    }

    @GetMapping("/todos")
    String todos(Model model) {
        model.addAttribute("todoForm", new TodoForm(""));
        return "todos";
    }

    @PostMapping("/todos")
    String create(@ModelAttribute("todoForm") TodoForm form, BindingResult bindingResult) {
        return bindingResult.hasErrors() ? "todos" : "redirect:/todos";
    }
}

record TodoForm(String title) {}
