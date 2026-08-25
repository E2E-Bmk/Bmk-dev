package integration.javamigrations;

import java.math.BigDecimal;
import org.apache.ibatis.migration.MigrationScript;

public final class V41_CreateChangelog implements MigrationScript {
  @Override public BigDecimal getId() { return new BigDecimal("41"); }
  @Override public String getDescription() { return "create java changelog"; }
  @Override public String getUpScript() {
    return "CREATE TABLE CHANGELOG (ID DECIMAL(20,0) NOT NULL PRIMARY KEY, APPLIED_AT VARCHAR(100) NOT NULL, DESCRIPTION VARCHAR(255) NOT NULL);";
  }
  @Override public String getDownScript() { return "DROP TABLE CHANGELOG;"; }
}
