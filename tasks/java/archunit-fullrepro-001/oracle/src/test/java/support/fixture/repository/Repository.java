package support.fixture.repository;

import support.fixture.model.DomainEntity;

public class Repository {
    public DomainEntity find() {
        return new DomainEntity("fixture");
    }
}
