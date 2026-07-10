# Submodule: Build System (Maven)

Maven-specific build migration steps. Called from [build.md](build.md).

## What to do

- [ ] Remove Spring Boot parent and replace with Jakarta EE / MicroProfile BOM
- [ ] Change packaging from `jar` to `war`
- [ ] Replace `spring-boot-maven-plugin` with `liberty-maven-plugin`
- [ ] Update `maven-compiler-plugin` for `{JAVA_VERSION}` and `-parameters` flag
- [ ] Add Jakarta EE 11 / MicroProfile provided-scope dependencies
- [ ] Replace Spring starters with Jakarta EE equivalents (use dependency-map.md)
- [ ] Remove unused Spring-only dependencies (`spring-boot-devtools`, etc.)
- [ ] Carry forward non-Spring runtime dependencies found in the original `pom.xml` (JDBC drivers, messaging clients, etc.) — see **Non-Spring Runtime Dependencies** below
- [ ] Create `src/main/liberty/config/server.xml` (handled in build.md)
- [ ] Compile: `./mvnw clean compile -DskipTests`

## pom.xml Reference Snippets

**Remove** the Spring Boot parent:
```xml
<!-- DELETE this -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>...</version>
</parent>
```

**Change** packaging to `war`:
```xml
<packaging>war</packaging>
```

**Add** properties:
```xml
<properties>
    <maven.compiler.release>{JAVA_VERSION}</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <liberty.var.app.context.root>/</liberty.var.app.context.root>
</properties>
```

**Add** Jakarta EE 11 and MicroProfile BOM in `<dependencyManagement>`:
```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>jakarta.platform</groupId>
            <artifactId>jakarta.jakartaee-bom</artifactId>
            <version>11.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
        <dependency>
            <groupId>org.eclipse.microprofile</groupId>
            <artifactId>microprofile</artifactId>
            <version>7.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

**Add** Jakarta EE 11 API dependency (provided — the runtime supplies the implementation):
```xml
<dependencies>
    <dependency>
        <groupId>jakarta.platform</groupId>
        <artifactId>jakarta.jakartaee-api</artifactId>
        <version>11.0.0</version>
        <scope>provided</scope>
    </dependency>
    <!-- MicroProfile API — provided by Open Liberty -->
    <dependency>
        <groupId>org.eclipse.microprofile</groupId>
        <artifactId>microprofile</artifactId>
        <version>7.0</version>
        <type>pom</type>
        <scope>provided</scope>
    </dependency>
    <!--
      Non-Spring runtime dependencies from the original pom.xml must be preserved here.
      Scan the original build file and add any of the following that were present.
      See the "Non-Spring Runtime Dependencies" reference table below.
    -->
</dependencies>
```

## Non-Spring Runtime Dependencies

Scan the original `pom.xml` for dependencies whose `groupId` does **not** start with `org.springframework` and that are not replaced by a Jakarta EE API. Carry them forward unchanged unless a newer version is required. Common examples:

> **Library placement**: If the dependency is a JDBC driver, MQ client, or any library that Liberty must reference from `server.xml` (e.g. via `<dataSource>` or `<jmsConnectionFactory>`), copy its JARs to `<server_name>/lib/<product>/` and use `<scope>provided</scope>` in `pom.xml` instead of `runtime`. See [dependency-map.md — Third-party Library Placement](../references/dependency-map.md) for per-product `server.xml` snippets.

| Dependency | Maven coordinates | Scope |
|---|---|---|
| **IBM DB2 JDBC** | `com.ibm.db2:jcc:{version}` | `runtime` |
| **Oracle JDBC** | `com.oracle.database.jdbc:ojdbc11:{version}` | `runtime` |
| **PostgreSQL JDBC** | `org.postgresql:postgresql:{version}` | `runtime` |
| **MySQL Connector/J** | `com.mysql:mysql-connector-j:{version}` | `runtime` |
| **Microsoft SQL Server JDBC** | `com.microsoft.sqlserver:mssql-jdbc:{version}` | `runtime` |
| **IBM MQ JMS client** | `com.ibm.mq:com.ibm.mq.allclient:{version}` | `runtime` |
| **ActiveMQ client** | `org.apache.activemq:activemq-client:{version}` | `runtime` |
| **Apache Kafka client** | `org.apache.kafka:kafka-clients:{version}` | `runtime` |
| **Bouncy Castle crypto** | `org.bouncycastle:bcprov-jdk18on:{version}` | `runtime` |
| **Lombok** | `org.projectlombok:lombok:{version}` | `provided` |
| **MapStruct** | `org.mapstruct:mapstruct:{version}` | `provided` |

> **Rule**: If the original build file contains a driver or client library that is not a Spring starter and is not part of Jakarta EE 11 or MicroProfile 7, copy it into the migrated `pom.xml` with the same (or latest compatible) version and `runtime` scope. Do not silently drop it.

**Example** — if the original `pom.xml` contains a DB2 driver and an MQ client:
```xml
<!-- DB2 JDBC driver — carry forward from original pom.xml -->
<dependency>
    <groupId>com.ibm.db2</groupId>
    <artifactId>jcc</artifactId>
    <version>11.5.9.0</version>
    <scope>runtime</scope>
</dependency>
<!-- IBM MQ JMS client — carry forward from original pom.xml -->
<dependency>
    <groupId>com.ibm.mq</groupId>
    <artifactId>com.ibm.mq.allclient</artifactId>
    <version>9.4.1.0</version>
    <scope>runtime</scope>
</dependency>
```

> **Do NOT use `io.openliberty:openliberty-kernel`**. Always use `io.openliberty:openliberty-runtime` when a Liberty runtime artifact must be referenced. The Liberty server installation is managed by the `liberty-maven-plugin` via `server.xml` — do not add it as a `<dependency>`.
>
> **Resolve the latest Open Liberty version** by fetching the IBM DHE release index and parsing the highest version directory:
> ```bash
> curl -s https://public.dhe.ibm.com/ibmdl/export/pub/software/openliberty/runtime/release/ \
>   | grep -oP '(?<=href=")[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(?=/)' \
>   | sort -V | tail -1
> ```
> Use the version returned as the `<version>` value for `io.openliberty:openliberty-runtime` and for the `runtimeVersion` property in the `liberty-maven-plugin` configuration.

**Add** the `liberty-maven-plugin`, `jandex-maven-plugin`, and update compiler/surefire:
```xml
<build>
    <finalName>${project.artifactId}</finalName>
    <plugins>
        <plugin>
            <groupId>io.openliberty.tools</groupId>
            <artifactId>liberty-maven-plugin</artifactId>
            <version>3.11.4</version>
            <configuration>
                <serverName>defaultServer</serverName>
            </configuration>
        </plugin>
        <plugin>
            <groupId>io.smallrye</groupId>
            <artifactId>jandex-maven-plugin</artifactId>
            <version>3.6</version>
            <executions>
                <execution>
                    <id>make-index</id>
                    <goals>
                        <goal>jandex</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.15.0</version>
            <configuration>
                <release>{JAVA_VERSION}</release>
                <compilerArgs>
                    <arg>-parameters</arg>
                </compilerArgs>
            </configuration>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-war-plugin</artifactId>
            <version>3.5.1</version>
            <configuration>
                <!-- Allow WAR without web.xml (Jakarta EE 11 / Servlet 6.1) -->
                <failOnMissingWebXml>false</failOnMissingWebXml>
            </configuration>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.5.6</version>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-failsafe-plugin</artifactId>
            <version>3.5.6</version>
            <executions>
                <execution>
                    <goals>
                        <goal>integration-test</goal>
                        <goal>verify</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

## Why Jandex?

The `jandex-maven-plugin` generates a Jandex index (`META-INF/jandex.idx`) during the `process-classes` phase. CDI 4.1 and JAX-RS 4.0 on Open Liberty use this index for fast annotation discovery at startup — without it, the runtime falls back to classpath scanning, which is slower and can miss beans that are not in the direct WAR archive.

The plugin runs automatically after compilation. No additional configuration is required for a standard Maven project.

## Liberty Maven Plugin Goals

| Goal | Description |
|---|---|
| `liberty:install-feature` | Install features declared in `server.xml` |
| `liberty:dev` | **Create server, deploy app, and start in dev mode (hot reload) — always use this** |
| `liberty:package` | Package server + app into a runnable JAR or ZIP |

## Testing the Application

Use `liberty:dev` to create the server, deploy the app, and start with hot reload in a single command:

```bash
# Creates server, deploys app, starts with hot reload — reloads automatically on source changes
./mvnw liberty:dev
```

Press `Enter` in the terminal to run tests while the server is running. Press `Ctrl+C` to stop.

## Complete Before/After Example

```xml
<!-- BEFORE: Spring Boot pom.xml snippet -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <!-- Non-Spring drivers/clients are carried forward as-is, e.g.: -->
    <dependency>
        <groupId>com.ibm.db2</groupId>
        <artifactId>jcc</artifactId>
        <version>11.5.9.0</version>
        <scope>runtime</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
        </plugin>
    </plugins>
</build>

<!-- AFTER: Open Liberty pom.xml snippet -->
<packaging>war</packaging>

<properties>
    <maven.compiler.release>{JAVA_VERSION}</maven.compiler.release>
    <liberty.var.app.context.root>/</liberty.var.app.context.root>
</properties>

<dependencies>
    <dependency>
        <groupId>jakarta.platform</groupId>
        <artifactId>jakarta.jakartaee-api</artifactId>
        <version>11.0.0</version>
        <scope>provided</scope>
    </dependency>
    <!-- Non-Spring runtime dependencies carried forward from original pom.xml -->
    <dependency>
        <groupId>com.ibm.db2</groupId>
        <artifactId>jcc</artifactId>
        <version>11.5.9.0</version>
        <scope>runtime</scope>
    </dependency>
</dependencies>

<build>
    <finalName>${project.artifactId}</finalName>
    <plugins>
        <plugin>
            <groupId>io.openliberty.tools</groupId>
            <artifactId>liberty-maven-plugin</artifactId>
            <version>3.12.0</version>
        </plugin>
        <plugin>
            <groupId>io.smallrye</groupId>
            <artifactId>jandex-maven-plugin</artifactId>
            <version>3.2.7</version>
            <executions>
                <execution>
                    <id>make-index</id>
                    <goals>
                        <goal>jandex</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-war-plugin</artifactId>
            <version>3.5.1</version>
            <configuration>
                <failOnMissingWebXml>false</failOnMissingWebXml>
            </configuration>
        </plugin>
    </plugins>
</build>
```
