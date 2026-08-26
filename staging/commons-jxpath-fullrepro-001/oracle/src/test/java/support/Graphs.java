package support;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.xml.parsers.DocumentBuilderFactory;
import org.apache.commons.jxpath.Pointer;
import org.w3c.dom.Document;

/** Caller-owned graph fixtures and small iteration helpers. */
public final class Graphs {

    private Graphs() {
    }

    public static class Address {
        private String city;
        private String zip;

        public Address() {
        }

        public Address(String city, String zip) {
            this.city = city;
            this.zip = zip;
        }

        public String getCity() {
            return city;
        }

        public void setCity(String city) {
            this.city = city;
        }

        public String getZip() {
            return zip;
        }

        public void setZip(String zip) {
            this.zip = zip;
        }
    }

    public static class Employee {
        private String name = "Ada";
        private int age = 36;
        private Address address;
        private List<String> phones = new ArrayList<>(List.of("111", "222", "333"));
        private Map<String, Object> props = new LinkedHashMap<>();

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public int getAge() {
            return age;
        }

        public void setAge(int age) {
            this.age = age;
        }

        public Address getAddress() {
            return address;
        }

        public void setAddress(Address address) {
            this.address = address;
        }

        public List<String> getPhones() {
            return phones;
        }

        public void setPhones(List<String> phones) {
            this.phones = phones;
        }

        public Map<String, Object> getProps() {
            return props;
        }

        public void setProps(Map<String, Object> props) {
            this.props = props;
        }
    }

    public static class Company {
        private List<Employee> employees = new ArrayList<>();

        public List<Employee> getEmployees() {
            return employees;
        }

        public void setEmployees(List<Employee> employees) {
            this.employees = employees;
        }
    }

    /** Standard employee: Ada, 36, phones [111, 222, 333], props {grade: senior}. */
    public static Employee employee() {
        Employee e = new Employee();
        e.getProps().put("grade", "senior");
        return e;
    }

    /** Standard company: Ada (36) and Bob (45). */
    public static Company company() {
        Company c = new Company();
        Employee ada = employee();
        Employee bob = employee();
        bob.setName("Bob");
        bob.setAge(45);
        c.getEmployees().add(ada);
        c.getEmployees().add(bob);
        return c;
    }

    /** Standard two-employee XML document. */
    public static Document companyXml() {
        return xml("<company><employee id=\"e1\"><name>Ada</name><age>36</age></employee>"
                + "<employee id=\"e2\"><name>Bob</name><age>45</age></employee></company>");
    }

    public static Document xml(String text) {
        try {
            return DocumentBuilderFactory.newInstance().newDocumentBuilder()
                    .parse(new ByteArrayInputStream(text.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    public static List<Object> drain(Iterator<?> iterator) {
        List<Object> values = new ArrayList<>();
        iterator.forEachRemaining(values::add);
        return values;
    }

    public static List<String> paths(Iterator<Pointer> pointers) {
        List<String> out = new ArrayList<>();
        pointers.forEachRemaining(p -> out.add(p.asPath()));
        return out;
    }

    /** Static functions exposed through ClassFunctions in tests. */
    public static class Util {
        public static String shout(String s) {
            return s.toUpperCase() + "!";
        }

        public static int triple(int n) {
            return n * 3;
        }
    }
}
