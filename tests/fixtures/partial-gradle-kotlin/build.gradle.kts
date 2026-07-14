plugins {
    id("org.springframework.boot") version "3.4.7"
    id("io.openliberty.tools.gradle.Liberty") version "3.9.2"
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    compileOnly("jakarta.platform:jakarta.jakartaee-api:11.0.0")
}
