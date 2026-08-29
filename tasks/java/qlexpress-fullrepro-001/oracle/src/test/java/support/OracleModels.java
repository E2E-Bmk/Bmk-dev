package support;

import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.annotation.QLAlias;
import com.alibaba.qlexpress4.annotation.QLFunction;
import com.alibaba.qlexpress4.exception.UserDefineException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public final class OracleModels {
    private OracleModels() {}

    public static boolean registerServiceMethod(Express4Runner runner, String name, Object service,
            String methodName, Class<?>... parameterTypes) throws Exception {
        Method threeArgument = null;
        for (Method method : Express4Runner.class.getMethods()) {
            if (!method.getName().equals("addFunctionOfServiceMethod")) {
                continue;
            }
            Class<?>[] parameters = method.getParameterTypes();
            if (parameters.length == 4
                    && parameters[0] == String.class
                    && parameters[1].isInstance(service)
                    && parameters[2] == String.class
                    && parameters[3].isAssignableFrom(Class[].class)) {
                return invokeRegistration(method, runner, name, service, methodName, parameterTypes);
            }
            if (parameters.length == 3
                    && parameters[0] == String.class
                    && parameters[1].isInstance(service)
                    && parameters[2] == String.class) {
                threeArgument = method;
            }
        }
        if (threeArgument != null) {
            return invokeRegistration(threeArgument, runner, name, service, methodName);
        }
        throw new NoSuchMethodException("addFunctionOfServiceMethod");
    }

    private static boolean invokeRegistration(Method method, Express4Runner runner, Object... arguments)
            throws Exception {
        try {
            return (Boolean)method.invoke(runner, arguments);
        }
        catch (InvocationTargetException error) {
            Throwable cause = error.getCause();
            if (cause instanceof RuntimeException) {
                throw (RuntimeException)cause;
            }
            if (cause instanceof Error) {
                throw (Error)cause;
            }
            throw error;
        }
    }

    public static UserDefineException businessException(String message) throws Exception {
        Constructor<?> messageOnly = null;
        for (Constructor<?> constructor : UserDefineException.class.getConstructors()) {
            Class<?>[] parameters = constructor.getParameterTypes();
            if (parameters.length == 2
                    && parameters[0] == UserDefineException.ExceptionType.class
                    && parameters[1] == String.class) {
                return (UserDefineException)constructor.newInstance(
                        UserDefineException.ExceptionType.BIZ_EXCEPTION, message);
            }
            if (parameters.length == 1 && parameters[0] == String.class) {
                messageOnly = constructor;
            }
        }
        if (messageOnly != null) {
            return (UserDefineException)messageOnly.newInstance(message);
        }
        throw new NoSuchMethodException("public UserDefineException construction path");
    }

    @QLAlias({"account"})
    public static class Account {
        @QLAlias({"credit"})
        public int balance;

        public Account(int balance) {
            this.balance = balance;
        }

        public int getBalance() {
            return balance;
        }

        public int bonus(int amount) {
            return balance + amount;
        }
    }

    public static class CalculatorService {
        public int triple(int value) {
            return value * 3;
        }
    }

    public static class AnnotatedFunctions {
        @QLFunction({"quad", "timesFour"})
        public static int quadruple(int value) {
            return value * 4;
        }
    }
}
