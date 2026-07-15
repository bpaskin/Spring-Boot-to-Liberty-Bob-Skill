# Module: Check JDK Version

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md).

Verify that the installed JDK meets the version requirement, derive the permitted target versions, and validate the explicit target Java version confirmed in the migration contract.

## Preconditions

This phase has no preconditions — it must **always** run as the very first step.

## Instructions

- **DO NOT** skip this phase.
- Jakarta EE 11 requires Java 17 or newer. This workflow targets the supported LTS JDKs **17**, **21**, and **25**.
- [ ] Check the installed Java runtime and compiler versions:
  ```bash
  java -version
  javac -version
  ```
- [ ] Parse the major versions. If `java` or `javac` is missing, their major versions differ, or the installed major is neither **17, 21, 25, nor greater than 25**:
    - **Warn the user**: "A matching JDK runtime and compiler at version 17, 21, 25, or newer than 25 are required by this workflow. Currently detected: java=<runtime version or 'none'>, javac=<compiler version or 'none'>. Install or activate one accepted JDK on PATH before retrying."
    - **Stop the migration** — do not proceed to any subsequent phase.
- [ ] Compute `ALLOWED_JAVA_VERSIONS` from the supported targets that are not higher than the installed JDK:

  | Installed JDK | Allowed target choices |
  |---|---|
  | 17 | 17 |
  | 21 | 17, 21 |
  | 25 | 17, 21, 25 |
  | Greater than 25 | 17, 21, 25 |

- [ ] During the consolidated migration contract, always ask the user to select one value from `ALLOWED_JAVA_VERSIONS`. Show both the detected JDK and the filtered choices. Do not infer a target from the build, choose the installed version automatically, or provide a default:

  > **Which Java version would you like to target for this migration?**
  > The installed JDK is `<detected version>`. You may target: `<ALLOWED_JAVA_VERSIONS>`.
  > Select one listed version. The target cannot be higher than the installed JDK.

- [ ] Stop before changing migration files until the question has an explicit answer. A previously confirmed migration contract that records the user's explicit answer satisfies this gate; never ask it a second time.
- [ ] Validate that the answer is in `ALLOWED_JAVA_VERSIONS`. If it is unsupported or higher than the installed JDK, reject it and re-prompt with only the allowed values.
- [ ] Record the user's answer as **`JAVA_VERSION`**. Use this value everywhere a Java version is required in the build files (Maven `<maven.compiler.release>`, `<release>`, Gradle `JavaVersion.VERSION_X`).
- [ ] If the contract does not contain an explicit answer, mark this gate `BLOCKED` and return to the consolidated contract question. Never infer or default `JAVA_VERSION`.
- [ ] Mark this phase as passed and proceed to the next phase.

## Notes

- Jakarta EE 11 has a Java 17 minimum. This workflow's migration targets remain capped at 17, 21, and 25. The installed JDK sets the ceiling when it is 25 or lower; any matching installed JDK newer than 25 exposes all three supported targets without making the newer major a target.
- IBM Semeru Runtimes (https://developer.ibm.com/languages/java/semeru-runtimes/) are the recommended JDK for production workloads on Open Liberty / WebSphere Liberty.
