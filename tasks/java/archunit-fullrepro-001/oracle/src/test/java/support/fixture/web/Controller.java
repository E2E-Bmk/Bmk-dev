package support.fixture.web;

import support.fixture.api.PublicApi;

public class Controller {
    private final PublicApi api = new PublicApi();

    public String handle() {
        return api.fetch();
    }
}
