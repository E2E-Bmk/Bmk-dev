package support;

import com.googlecode.cqengine.attribute.MultiValueAttribute;
import com.googlecode.cqengine.attribute.SimpleAttribute;
import com.googlecode.cqengine.attribute.SimpleNullableAttribute;
import com.googlecode.cqengine.query.option.QueryOptions;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/** A deliberately non-automotive value object used by the CQEngine oracle. */
public class Item implements Serializable {
    private static final long serialVersionUID = 1L;

    public static final SimpleAttribute<Item, Integer> ID =
            new SimpleAttribute<Item, Integer>(Item.class, Integer.class, "id") {
                @Override
                public Integer getValue(Item object, QueryOptions queryOptions) {
                    return object.id;
                }
            };

    public static final SimpleAttribute<Item, String> NAME =
            new SimpleAttribute<Item, String>(Item.class, String.class, "name") {
                @Override
                public String getValue(Item object, QueryOptions queryOptions) {
                    return object.name;
                }
            };

    public static final SimpleAttribute<Item, Integer> SCORE =
            new SimpleAttribute<Item, Integer>(Item.class, Integer.class, "score") {
                @Override
                public Integer getValue(Item object, QueryOptions queryOptions) {
                    return object.score;
                }
            };

    public static final SimpleAttribute<Item, String> CATEGORY =
            new SimpleAttribute<Item, String>(Item.class, String.class, "category") {
                @Override
                public String getValue(Item object, QueryOptions queryOptions) {
                    return object.category;
                }
            };

    public static final SimpleNullableAttribute<Item, Integer> RANK =
            new SimpleNullableAttribute<Item, Integer>(Item.class, Integer.class, "rank") {
                @Override
                public Integer getValue(Item object, QueryOptions queryOptions) {
                    return object.rank;
                }
            };

    public static final MultiValueAttribute<Item, String> TAGS =
            new MultiValueAttribute<Item, String>(Item.class, String.class, "tags") {
                @Override
                public Iterable<String> getValues(Item object, QueryOptions queryOptions) {
                    return object.tags;
                }
            };

    public final int id;
    public final String name;
    public final int score;
    public final String category;
    public final Integer rank;
    public final List<String> tags;

    public Item(int id, String name, int score, String category, Integer rank, String... tags) {
        this.id = id;
        this.name = Objects.requireNonNull(name, "name");
        this.score = score;
        this.category = Objects.requireNonNull(category, "category");
        this.rank = rank;
        this.tags = Collections.unmodifiableList(new ArrayList<String>(Arrays.asList(tags)));
    }

    @Override
    public boolean equals(Object other) {
        return other instanceof Item && id == ((Item) other).id;
    }

    @Override
    public int hashCode() {
        return id;
    }
}
