package support.fixture.cycle.alpha;

import support.fixture.cycle.beta.Beta;

public class Alpha {
    public Beta beta() {
        return new Beta();
    }
}
