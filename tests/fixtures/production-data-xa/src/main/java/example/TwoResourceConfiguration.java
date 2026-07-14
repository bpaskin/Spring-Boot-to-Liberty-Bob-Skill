package example;

import org.postgresql.xa.PGXADataSource;
import org.springframework.context.annotation.Configuration;

@Configuration
class TwoResourceConfiguration {
    PGXADataSource orders() { return new PGXADataSource(); }
    PGXADataSource billing() { return new PGXADataSource(); }
}
