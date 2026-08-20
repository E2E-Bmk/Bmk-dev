package support;

import javax.sql.DataSource;
import java.io.PrintWriter;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;

/** Deterministic caller-owned JDBC carrier using only standard public JDBC APIs. */
public final class ControllableDataSource implements DataSource {
   public final AtomicInteger uncredentialedCalls = new AtomicInteger();
   public final AtomicInteger credentialedCalls = new AtomicInteger();
   public final AtomicInteger physicalCloses = new AtomicInteger();
   public final AtomicInteger rollbacks = new AtomicInteger();
   public final AtomicInteger commits = new AtomicInteger();
   public final AtomicInteger statementsCreated = new AtomicInteger();
   public final AtomicInteger statementsClosed = new AtomicInteger();
   public final AtomicInteger clearWarningsCalls = new AtomicInteger();
   public final List<PhysicalState> physicalStates = new ArrayList<>();
   public volatile String lastUsername;
   public volatile String lastPassword;
   public volatile boolean failConnections;
   public volatile boolean valid = true;
   private volatile PrintWriter logWriter;
   private volatile int loginTimeout;

   @Override
   public Connection getConnection() throws SQLException {
      uncredentialedCalls.incrementAndGet();
      return createConnection();
   }

   @Override
   public Connection getConnection(String username, String password) throws SQLException {
      credentialedCalls.incrementAndGet();
      lastUsername = username;
      lastPassword = password;
      return createConnection();
   }

   public synchronized PhysicalState lastPhysicalState() {
      return physicalStates.get(physicalStates.size() - 1);
   }

   private synchronized Connection createConnection() throws SQLException {
      if (failConnections) {
         throw new SQLException("carrier connection unavailable");
      }
      PhysicalState state = new PhysicalState();
      physicalStates.add(state);
      InvocationHandler handler = (proxy, method, args) -> invokeConnection(state, proxy, method, args);
      return (Connection) Proxy.newProxyInstance(
         ControllableDataSource.class.getClassLoader(), new Class<?>[]{Connection.class}, handler);
   }

   private Object invokeConnection(PhysicalState state, Object proxy, Method method, Object[] args) throws SQLException {
      String name = method.getName();
      switch (name) {
         case "close": state.closed = true; physicalCloses.incrementAndGet(); return null;
         case "abort": state.closed = true; physicalCloses.incrementAndGet(); return null;
         case "isClosed": return state.closed;
         case "isValid": return valid && !state.closed;
         case "getAutoCommit": return state.autoCommit;
         case "setAutoCommit": state.autoCommit = (Boolean) args[0]; return null;
         case "isReadOnly": return state.readOnly;
         case "setReadOnly": state.readOnly = (Boolean) args[0]; return null;
         case "getTransactionIsolation": return state.transactionIsolation;
         case "setTransactionIsolation": state.transactionIsolation = (Integer) args[0]; return null;
         case "getCatalog": return state.catalog;
         case "setCatalog": state.catalog = (String) args[0]; return null;
         case "getSchema": return state.schema;
         case "setSchema": state.schema = (String) args[0]; return null;
         case "getNetworkTimeout": return state.networkTimeout;
         case "setNetworkTimeout": state.networkTimeout = (Integer) args[1]; return null;
         case "rollback": rollbacks.incrementAndGet(); return null;
         case "commit": commits.incrementAndGet(); return null;
         case "clearWarnings": clearWarningsCalls.incrementAndGet(); return null;
         case "getWarnings": return null;
         case "beginRequest": case "endRequest": return null;
         case "createStatement": statementsCreated.incrementAndGet(); return createStatement((Connection) proxy);
         case "unwrap":
            if (((Class<?>) args[0]).isInstance(proxy)) return ((Class<?>) args[0]).cast(proxy);
            throw new SQLException("not a wrapper");
         case "isWrapperFor": return ((Class<?>) args[0]).isInstance(proxy);
         case "toString": return "public-jdbc-carrier-" + physicalStates.indexOf(state);
         case "hashCode": return System.identityHashCode(proxy);
         case "equals": return proxy == args[0];
         default: return defaultValue(method.getReturnType());
      }
   }

   private Statement createStatement(Connection connection) {
      final boolean[] closed = {false};
      InvocationHandler handler = (proxy, method, args) -> {
         switch (method.getName()) {
            case "execute": return true;
            case "executeUpdate": return 1;
            case "close": closed[0] = true; statementsClosed.incrementAndGet(); return null;
            case "isClosed": return closed[0];
            case "getConnection": return connection;
            case "unwrap":
               if (((Class<?>) args[0]).isInstance(proxy)) return ((Class<?>) args[0]).cast(proxy);
               throw new SQLException("not a wrapper");
            case "isWrapperFor": return ((Class<?>) args[0]).isInstance(proxy);
            default: return defaultValue(method.getReturnType());
         }
      };
      return (Statement) Proxy.newProxyInstance(
         ControllableDataSource.class.getClassLoader(), new Class<?>[]{Statement.class}, handler);
   }

   private static Object defaultValue(Class<?> type) {
      if (!type.isPrimitive()) return null;
      if (type == boolean.class) return false;
      if (type == byte.class) return (byte) 0;
      if (type == short.class) return (short) 0;
      if (type == int.class) return 0;
      if (type == long.class) return 0L;
      if (type == float.class) return 0F;
      if (type == double.class) return 0D;
      if (type == char.class) return '\0';
      return null;
   }

   @Override public PrintWriter getLogWriter() { return logWriter; }
   @Override public void setLogWriter(PrintWriter out) { logWriter = out; }
   @Override public void setLoginTimeout(int seconds) { loginTimeout = seconds; }
   @Override public int getLoginTimeout() { return loginTimeout; }
   @Override public Logger getParentLogger() throws SQLFeatureNotSupportedException { throw new SQLFeatureNotSupportedException(); }
   @Override public <T> T unwrap(Class<T> iface) throws SQLException {
      if (iface.isInstance(this)) return iface.cast(this);
      throw new SQLException("not a wrapper");
   }
   @Override public boolean isWrapperFor(Class<?> iface) { return iface.isInstance(this); }

   /** Observable physical state owned by the caller-side JDBC carrier. */
   public static final class PhysicalState {
      public boolean closed;
      public boolean autoCommit = true;
      public boolean readOnly;
      public int transactionIsolation = Connection.TRANSACTION_READ_COMMITTED;
      public String catalog;
      public String schema;
      public int networkTimeout;
   }
}
