package example;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

class CsrfGuardTest {
    @Test void acceptsValidToken() {
        assertTrue(CsrfGuard.accepts("known", "known"));
    }

    @Test void rejectsMissingToken() {
        assertFalse(CsrfGuard.accepts("known", null)); // missing token
    }

    @Test void rejectsInvalidToken() {
        assertFalse(CsrfGuard.accepts("known", "wrong")); // invalid token
    }
}
