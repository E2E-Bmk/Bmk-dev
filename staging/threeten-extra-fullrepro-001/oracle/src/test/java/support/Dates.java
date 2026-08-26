package support;

import java.time.Instant;
import java.time.LocalDate;

/** Shared fixture instants and dates for the threeten-extra oracle. */
public final class Dates {

    private Dates() {
    }

    public static Instant instant(String text) {
        return Instant.parse(text);
    }

    public static LocalDate date(int year, int month, int day) {
        return LocalDate.of(year, month, day);
    }
}
