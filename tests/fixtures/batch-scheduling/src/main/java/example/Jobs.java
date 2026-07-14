package example;

import org.springframework.scheduling.annotation.Scheduled;

class Jobs {
    @Scheduled(cron = "0 0 * * * *", zone = "America/New_York")
    void hourly() {}
}
