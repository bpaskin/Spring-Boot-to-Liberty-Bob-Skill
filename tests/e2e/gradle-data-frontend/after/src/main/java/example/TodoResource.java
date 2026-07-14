package example;

import jakarta.enterprise.context.RequestScoped;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;

@Path("/todos")
@RequestScoped
public class TodoResource {
    @GET
    public String form() {
        return "<form method='post'><input type='hidden' name='_csrf'></form>";
    }
}
