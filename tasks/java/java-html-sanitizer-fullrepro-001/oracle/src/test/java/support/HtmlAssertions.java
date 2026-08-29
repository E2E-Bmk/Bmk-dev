package support;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Order- and whitespace-insensitive assertions for public rendered HTML. */
public final class HtmlAssertions {
  private static final Pattern ATTRIBUTE =
      Pattern.compile("([A-Za-z][A-Za-z0-9:-]*)\\s*=\\s*\"([^\"]*)\"");

  private HtmlAssertions() {}

  public static Set<String> attributePairs(String html) {
    Set<String> pairs = new HashSet<String>();
    Matcher matcher = ATTRIBUTE.matcher(html);
    while (matcher.find()) {
      pairs.add(matcher.group(1).toLowerCase(Locale.ROOT) + "=" + matcher.group(2));
    }
    return pairs;
  }

  public static Set<String> relTokens(String html) {
    Matcher matcher = Pattern.compile("\\brel\\s*=\\s*\"([^\"]*)\"").matcher(html);
    assertTrue(matcher.find(), "expected a rel attribute");
    Set<String> tokens = new HashSet<String>();
    for (String token : matcher.group(1).trim().split("\\s+")) {
      if (!token.isEmpty()) tokens.add(token.toLowerCase(Locale.ROOT));
    }
    return tokens;
  }

  public static void assertContainsAttributes(String html, String... expected) {
    assertTrue(attributePairs(html).containsAll(Arrays.asList(expected)));
  }

  public static void assertTagPresent(String html, String tag) {
    assertTrue(html.toLowerCase(Locale.ROOT).contains("<" + tag.toLowerCase(Locale.ROOT)));
  }

  public static void assertTagAbsent(String html, String tag) {
    assertFalse(html.toLowerCase(Locale.ROOT).contains("<" + tag.toLowerCase(Locale.ROOT)));
  }

  public static void assertTextProjection(String expected, String html) {
    assertEquals(expected, html.replaceAll("<[^>]*>", ""));
  }
}
