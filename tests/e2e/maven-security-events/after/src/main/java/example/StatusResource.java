package example;

import jakarta.annotation.security.PermitAll;
import jakarta.annotation.security.RolesAllowed;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;

@Path("/status")
@ApplicationScoped
public class StatusResource {
    @GET
    @PermitAll
    public String status() {
        return "ok";
    }

    @GET
    @Path("/admin")
    @RolesAllowed("ADMIN")
    public String admin() {
        return "admin";
    }
}
