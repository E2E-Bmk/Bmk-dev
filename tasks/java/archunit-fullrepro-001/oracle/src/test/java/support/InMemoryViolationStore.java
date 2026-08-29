package support;

import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.library.freeze.ViolationStore;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

public class InMemoryViolationStore implements ViolationStore {
    public Properties initializedWith = new Properties();
    public int saves;
    private final Map<String, List<String>> lines = new LinkedHashMap<>();

    @Override
    public void initialize(Properties properties) {
        initializedWith = new Properties();
        initializedWith.putAll(properties);
    }

    @Override
    public boolean contains(ArchRule rule) {
        return lines.containsKey(rule.getDescription());
    }

    @Override
    public void save(ArchRule rule, List<String> violations) {
        saves++;
        lines.put(rule.getDescription(), new ArrayList<>(violations));
    }

    @Override
    public List<String> getViolations(ArchRule rule) {
        return Collections.unmodifiableList(lines.get(rule.getDescription()));
    }
}
