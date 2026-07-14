package example;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

class GreetingServiceTest {
    @Test
    void preservesGreeting() {
        assertEquals("hello", new GreetingService().message());
    }
}
