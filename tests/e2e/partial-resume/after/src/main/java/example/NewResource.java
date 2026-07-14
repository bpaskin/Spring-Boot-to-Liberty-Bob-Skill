package example;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;

@Path("/new")
public class NewResource {
    @GET
    public String value() { return "new"; }
}
