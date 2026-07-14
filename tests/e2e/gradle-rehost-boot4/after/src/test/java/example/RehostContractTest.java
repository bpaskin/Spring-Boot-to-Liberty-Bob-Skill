package example;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

class RehostContractTest {
    @Test void controllerContractIsStable() {
        assertEquals("boot4-on-liberty", new HelloController().hello());
    }
}
