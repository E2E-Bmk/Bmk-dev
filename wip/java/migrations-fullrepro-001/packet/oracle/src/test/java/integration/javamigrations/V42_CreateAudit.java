package integration.javamigrations;

import java.math.BigDecimal;
import org.apache.ibatis.migration.MigrationScript;

public final class V42_CreateAudit implements MigrationScript {
  @Override public BigDecimal getId() { return new BigDecimal("42"); }
  @Override public String getDescription() { return "create java audit"; }
  @Override public String getUpScript() { return "CREATE TABLE JAVA_AUDIT(ID DECIMAL(20,0) PRIMARY KEY);"; }
  @Override public String getDownScript() { return "DROP TABLE JAVA_AUDIT;"; }
}
