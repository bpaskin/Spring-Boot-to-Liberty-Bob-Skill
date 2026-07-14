package example;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.ws.server.endpoint.annotation.Endpoint;

@Endpoint
class LegacyAdapters {
    RedisTemplate<String, String> cache;
}
