package support;

import java.sql.Connection;
import java.sql.Driver;
import java.sql.DriverPropertyInfo;
import java.sql.SQLException;
import java.util.Properties;
import java.util.logging.Logger;

/** Minimal caller-owned JDBC Driver used only for public source-selection validation. */
public final class PublicDriver implements Driver {
   @Override public Connection connect(String url, Properties info) { return null; }
   @Override public boolean acceptsURL(String url) { return false; }
   @Override public DriverPropertyInfo[] getPropertyInfo(String url, Properties info) { return new DriverPropertyInfo[0]; }
   @Override public int getMajorVersion() { return 1; }
   @Override public int getMinorVersion() { return 0; }
   @Override public boolean jdbcCompliant() { return false; }
   @Override public Logger getParentLogger() { return Logger.getGlobal(); }
}
