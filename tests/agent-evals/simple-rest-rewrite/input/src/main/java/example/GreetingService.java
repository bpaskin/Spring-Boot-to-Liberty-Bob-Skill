package example;

import org.springframework.stereotype.Service;

@Service
public class GreetingService {
    public String message() {
        return "hello";
    }
}
