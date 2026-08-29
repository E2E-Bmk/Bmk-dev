package support;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.owasp.html.HtmlChangeListener;

/** Public listener that records canonical notification payloads. */
public final class RecordingListener implements HtmlChangeListener<String> {
  public final List<String> tags = new ArrayList<String>();
  public final List<String> attributes = new ArrayList<String>();

  @Override public void discardedTag(String context, String name) {
    tags.add(context + ":" + name);
  }

  @Override public void discardedAttributes(
      String context, String name, String... attributeNames) {
    String[] copy = attributeNames.clone();
    Arrays.sort(copy);
    attributes.add(context + ":" + name + ":" + Arrays.asList(copy));
  }
}
