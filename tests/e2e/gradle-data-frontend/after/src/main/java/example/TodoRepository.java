package example;

import jakarta.data.repository.CrudRepository;
import jakarta.data.repository.Repository;

@Repository(dataStore = "TodoStore")
public interface TodoRepository extends CrudRepository<Todo, Long> {}
