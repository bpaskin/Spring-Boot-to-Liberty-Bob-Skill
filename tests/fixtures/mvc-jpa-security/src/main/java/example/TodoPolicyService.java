package example;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;

@Service
class TodoPolicyService {
    @PreAuthorize("hasRole('ADMIN') or (authentication.name == #owner and @tenantPolicy.allows(#tenant))")
    void update(String owner, String tenant) {
    }
}
