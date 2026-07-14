package example;

public final class CsrfGuard {
    private CsrfGuard() {}

    public static boolean accepts(String expected, String supplied) {
        return expected != null && supplied != null && expected.equals(supplied);
    }
}
