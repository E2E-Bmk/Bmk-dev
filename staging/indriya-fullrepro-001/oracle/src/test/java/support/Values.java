package support;

import javax.measure.Quantity;

/** Shared observation helpers for the measurement oracle. */
public final class Values {

    private Values() {
    }

    /** Value of a quantity observed through its double view. */
    public static double dbl(Quantity<?> quantity) {
        return quantity.getValue().doubleValue();
    }

    /** Decimal string of a quantity's numeric value (integral values render without a point). */
    public static String num(Quantity<?> quantity) {
        return String.valueOf(quantity.getValue());
    }
}
