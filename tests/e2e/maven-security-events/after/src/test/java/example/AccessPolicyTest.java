package example;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

class AccessPolicyTest {
    @Test void anonymousIsUnauthorized() {
        int status = AccessPolicy.status(null, false, "alice");
        assertEquals(401, status); // status == 401
    }

    @Test void wrongUserIsForbidden() {
        int status = AccessPolicy.status("bob", false, "alice");
        assertEquals(403, status); // status == 403
    }

    @Test void ownerAndAdminAreAllowed() {
        assertEquals(200, AccessPolicy.status("alice", false, "alice"));
        assertEquals(200, AccessPolicy.status("admin", true, "alice"));
    }
}
