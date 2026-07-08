# Module: Check JDK Version

Verify that the installed JDK meets the version requirement and confirm the target Java version with the user before proceeding with the migration.

## Preconditions

This phase has no preconditions — it must **always** run as the very first step.

## Instructions

- **DO NOT** skip this phase.
- The valid supported Java versions for this migration are **17**, **21**, and **25**.
- [ ] Check the installed JDK version:
  ```bash
  java -version
  ```
- [ ] If the detected version is **not one of 17, 21, or 25** or `java` is not found:
    - **Warn the user**: "A supported JDK version (17, 21, or 25) is required. Currently installed: <detected version or 'none'>. Please install one of the supported versions and ensure it is on your PATH before retrying."
    - **Stop the migration** — do not proceed to any subsequent phase.
- [ ] If the detected version is one of **17, 21, or 25**, ask the user:

  > **Which Java version would you like to target for this migration?**
  > The installed JDK is `<detected version>`. Supported options are **17**, **21**, and **25**.
  > Please enter one of: `17`, `21`, `25`:

- [ ] Validate the answer is one of `17`, `21`, `25`. If the user enters anything else, re-prompt.
- [ ] Record the user's answer as **`JAVA_VERSION`**. Use this value everywhere a Java version is required in the build files (Maven `<maven.compiler.release>`, `<release>`, Gradle `JavaVersion.VERSION_X`).
- [ ] If the user does not specify a version, default to **21**.
- [ ] Mark this phase as passed and proceed to the next phase.

## Notes

- Open Liberty supports JDK 17, 21, and 25.
- IBM Semeru Runtimes (https://developer.ibm.com/languages/java/semeru-runtimes/) are the recommended JDK for production workloads on Open Liberty / WebSphere Liberty.
