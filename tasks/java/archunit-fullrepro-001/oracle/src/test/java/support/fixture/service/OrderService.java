package support.fixture.service;

import support.fixture.model.DomainEntity;
import support.fixture.repository.Repository;

public class OrderService extends BaseService implements Runnable {
    public Repository repository = new Repository();

    @Override
    public String load() {
        DomainEntity entity = repository.find();
        return entity.name();
    }

    @Override
    public void run() {
        load();
    }
}
