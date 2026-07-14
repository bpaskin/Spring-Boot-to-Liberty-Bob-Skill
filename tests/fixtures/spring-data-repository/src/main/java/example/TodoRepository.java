package example;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

interface TodoRepository extends JpaRepository<Todo, Long> {
    List<Todo> findByCompleted(boolean completed);
}

class Todo {
    Long id;
    boolean completed;
}
