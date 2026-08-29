package support;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import support.fixture.api.PublicApi;
import support.fixture.isolated.Independent;
import support.fixture.model.DomainEntity;
import support.fixture.repository.Repository;
import support.fixture.service.BaseService;
import support.fixture.service.OrderService;
import support.fixture.web.Controller;

public final class OracleSupport {
    private OracleSupport() {
    }

    public static JavaClasses graph() {
        return new ClassFileImporter().importClasses(
                PublicApi.class, Controller.class, OrderService.class, BaseService.class,
                Repository.class, DomainEntity.class, Independent.class);
    }
}
