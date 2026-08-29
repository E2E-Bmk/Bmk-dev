package support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.owasp.html.HtmlStreamEventReceiver;

/** Public event sink used to inspect only receiver-visible behavior. */
public class RecordingReceiver implements HtmlStreamEventReceiver {
  public final List<String> events = new ArrayList<String>();
  public boolean closed;

  @Override public void openDocument() { events.add("openDocument"); }
  @Override public void closeDocument() { events.add("closeDocument"); }
  @Override public void openTag(String elementName, List<String> attrs) {
    events.add("open:" + elementName + ":" + new ArrayList<String>(attrs));
  }
  @Override public void closeTag(String elementName) { events.add("close:" + elementName); }
  @Override public void text(String text) { events.add("text:" + text); }

  public List<String> snapshot() {
    return Collections.unmodifiableList(new ArrayList<String>(events));
  }
}
