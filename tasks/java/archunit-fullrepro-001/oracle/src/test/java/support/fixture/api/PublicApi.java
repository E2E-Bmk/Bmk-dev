package support.fixture.api;

import support.fixture.service.OrderService;

public class PublicApi {
    private final OrderService service = new OrderService();

    public String fetch() {
        return service.load();
    }
}
