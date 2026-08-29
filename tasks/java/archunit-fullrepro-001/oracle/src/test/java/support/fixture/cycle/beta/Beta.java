package support.fixture.cycle.beta;

import support.fixture.cycle.alpha.Alpha;

public class Beta {
    public Alpha alpha() {
        return new Alpha();
    }
}
