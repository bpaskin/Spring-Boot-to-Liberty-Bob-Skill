package example;

import java.util.Locale;
import java.util.Map;

final class WebConfiguration {
    private static final String LOCALE_ATTRIBUTE = "locale";

    Locale resolveLocale(Map<String, Object> session, Locale requestLocale) {
        Object selected = session.get(LOCALE_ATTRIBUTE);
        return selected instanceof Locale locale ? locale : requestLocale;
    }
}
