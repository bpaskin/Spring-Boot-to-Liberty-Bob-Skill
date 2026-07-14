# Module: Check JDK Version

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md).

Verify that the installed JDK meets the version requirement and apply the target Java version already confirmed in the migration contract.

## Preconditions

This phase has no preconditions — it must **always** run as the very first step.

## Instructions

- **DO NOT** skip this phase.
- Jakarta EE 11 requires Java 17 or newer. This workflow targets the supported LTS JDKs **17**, **21**, and **25**.
- [ ] Check the installed JDK version:
  ```bash
  java -version
  ```
- [ ] If the detected version is **not one of 17, 21, or 25** or `java` is not found:
    - **Warn the user**: "A supported JDK version (17, 21, or 25) is required. Currently installed: <detected version or 'none'>. Please install one of the supported versions and ensure it is on your PATH before retrying."
    - **Stop the migration** — do not proceed to any subsequent phase.
- [ ] If the detected version is one of **17, 21, or 25**, use the contract value. Ask only if the contract is missing or the detected environment cannot run the selected target:

  > **Which Java version would you like to target for this migration?**
  > The installed JDK is `<detected version>`. Supported options are **17**, **21**, and **25**.
  > Please enter one of: `17`, `21`, `25`:

- [ ] Validate the answer is one of `17`, `21`, `25`. If the user enters anything else, re-prompt.
- [ ] Record the user's answer as **`JAVA_VERSION`**. Use this value everywhere a Java version is required in the build files (Maven `<maven.compiler.release>`, `<release>`, Gradle `JavaVersion.VERSION_X`).
- [ ] If the contract does not specify a version, propose **21** in the consolidated contract rather than pausing again inside this module.
- [ ] Mark this phase as passed and proceed to the next phase.

## Notes

- Jakarta EE 11 has a Java 17 minimum. Open Liberty supports JDK 17, 21, and 25 for this workflow; default to 21 when the project has no documented runtime policy.
- IBM Semeru Runtimes (https://developer.ibm.com/languages/java/semeru-runtimes/) are the recommended JDK for production workloads on Open Liberty / WebSphere Liberty.
