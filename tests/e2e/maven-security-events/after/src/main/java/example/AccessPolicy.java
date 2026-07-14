package example;

final class AccessPolicy {
    private AccessPolicy() {}

    static int status(String principal, boolean admin, String owner) {
        if (principal == null) return 401;
        if (!admin && !principal.equals(owner)) return 403;
        return 200;
    }
}
